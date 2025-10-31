"""
compare_tmdl.py

Comparar a pasta de 2 Power BI TMDL semantic model:
- encontra a pasta *.SemanticModel em cada modelo
- entra em definition/tables (ou definition)
- lista e lê todos os arquivos .tmdl
- compara tabelas, colunas e medidas
- mostra resumo e detalhes de diferenças

Execute: python compare_tmdl.py
"""
# importando os pacotes
import os
import sys
import json
import difflib
import re
from pathlib import Path

def pick_folder_gui(prompt="Selecione uma pasta (pressione Cancel para digitar o caminho):"):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory(title=prompt)
        root.destroy()
        if path:
            return path
    except Exception:
        pass
    # fallback to text input
    return input(f"{prompt}\nCaminho: ").strip()

# 1) localizar pasta *.SemanticModel dentro do caminho informado (recursivo, retorna primeiro achado)
def find_semantic_model_folder(root_path: str):
    root = Path(root_path)
    if not root.exists():
        return None
    # search for folder name that endswith .SemanticModel (case-insensitive)
    for p in root.rglob("*"):
        if p.is_dir() and p.name.lower().endswith(".semanticmodel"):
            return str(p)
    # also allow when user already passed the .SemanticModel folder
    if root.name.lower().endswith(".semanticmodel") and root.is_dir():
        return str(root)
    return None

# 2) chegar na pasta definition/tables (ou definition)
def get_definition_tables_folder(semantic_model_folder: str):
    cand1 = Path(semantic_model_folder) / "definition" / "tables"
    cand2 = Path(semantic_model_folder) / "definition"
    if cand1.exists() and cand1.is_dir():
        return str(cand1)
    if cand2.exists() and cand2.is_dir():
        return str(cand2)
    return None

# 3) listar arquivos .tmdl nessa pasta
def list_tmdl_files(def_tables_folder: str):
    p = Path(def_tables_folder)
    files = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() == ".tmdl"]
    return sorted(files, key=lambda x: x.name.lower())

# 4) tentar parse do .tmdl: se for JSON, parse; senão fallback para parsing textual simples
def parse_tmdl_file(path: Path):
    """
    Lê um arquivo .tmdl no formato textual (não JSON).
    Extrai:
    - table name
    - column names
    - measure names
    """
    text = path.read_text(encoding="utf-8", errors="ignore")

    columns = set()
    measures = set()

    # regex patterns baseados no formato textual do TMDL
    table_pattern = re.compile(r"^\s*table\s+([A-Za-z0-9_ ]+)", re.MULTILINE)
    column_pattern = re.compile(r"^\s*column\s+([A-Za-z0-9_]+)", re.MULTILINE)
    measure_pattern = re.compile(r"^\s*measure\s+'?([^'=]+?)'?\s*=", re.MULTILINE)

    # capturar nomes
    tables = table_pattern.findall(text)
    columns = set(column_pattern.findall(text))
    measures = set(measure_pattern.findall(text))

    # garantir que o nome da tabela principal seja o nome do arquivo (quando possível)
    name = path.stem
    if tables:
        # se o nome da primeira tabela for diferente do arquivo, use o do arquivo
        name = tables[0].strip()

    return {
        "name": name,
        "file": str(path),
        "text": text,
        "columns": columns,
        "measures": measures,
        "raw_json": None  # não é JSON, mas deixamos o campo para compatibilidade
    }


# 5) comparar dois conjuntos de parse results
def compare_models(source_files, target_files):
    """
    source_files, target_files: dict nome -> parse_result
    retorna um dict com resumo e diffs detalhados
    """
    source_names = set(source_files.keys())
    target_names = set(target_files.keys())

    only_in_source = sorted(source_names - target_names)
    only_in_target = sorted(target_names - source_names)
    common = sorted(source_names & target_names)

    identical = []
    different = []

    diffs_details = {}

    for name in common:
        src = source_files[name]
        tgt = target_files[name]
        # quick check: exact text equality
        if src["text"] == tgt["text"]:
            identical.append(name)
            continue
        # else compare parsed columns/measures
        src_cols = src["columns"]
        tgt_cols = tgt["columns"]
        src_meas = src["measures"]
        tgt_meas = tgt["measures"]

        cols_only_src = sorted(src_cols - tgt_cols)
        cols_only_tgt = sorted(tgt_cols - src_cols)
        meas_only_src = sorted(src_meas - tgt_meas)
        meas_only_tgt = sorted(tgt_meas - src_meas)

        # fallback: if parsed sets empty, produce a textual diff snippet to show
        textual_diff = []
        if not (src_cols or tgt_cols or src_meas or tgt_meas):
            # produce a small unified diff snippet (first 200 lines)
            text_diff = difflib.unified_diff(
                src["text"].splitlines(keepends=True),
                tgt["text"].splitlines(keepends=True),
                fromfile=f"{name} (source)",
                tofile=f"{name} (target)",
                lineterm=""
            )
            textual_diff = list(text_diff)[:400]  # limit
        # decide if "different"
        if cols_only_src or cols_only_tgt or meas_only_src or meas_only_tgt or textual_diff:
            different.append(name)
            diffs_details[name] = {
                "cols_only_in_source": cols_only_src,
                "cols_only_in_target": cols_only_tgt,
                "measures_only_in_source": meas_only_src,
                "measures_only_in_target": meas_only_tgt,
                "textual_diff_snippet": textual_diff
            }
        else:
            identical.append(name)

    result = {
        "counts": {
            "source_total": len(source_names),
            "target_total": len(target_names),
            "identical": len(identical),
            "different": len(different),
            "only_in_source": len(only_in_source),
            "only_in_target": len(only_in_target)
        },
        "lists": {
            "identical": identical,
            "different": different,
            "only_in_source": only_in_source,
            "only_in_target": only_in_target
        },
        "details": diffs_details
    }
    return result

# 6) run flow
def main():
    print("=== Comparador de modelos .tmdl ===")
    print("Escolha o Modelo A (fonte):")
    model_a_root = pick_folder_gui("Selecione a pasta raiz do Modelo A (ou digite o caminho)")
    if not model_a_root:
        print("Nenhum caminho informado para Modelo A. Saindo.")
        sys.exit(1)
    print("Escolha o Modelo B (central):")
    model_b_root = pick_folder_gui("Selecione a pasta raiz do Modelo B (ou digite o caminho)")
    if not model_b_root:
        print("Nenhum caminho informado para Modelo B. Saindo.")
        sys.exit(1)

    # localizar .SemanticModel
    a_sem = find_semantic_model_folder(model_a_root)
    b_sem = find_semantic_model_folder(model_b_root)
    if not a_sem:
        print(f"ERRO: não encontrei pasta *.SemanticModel dentro de: {model_a_root}")
        sys.exit(1)
    if not b_sem:
        print(f"ERRO: não encontrei pasta *.SemanticModel dentro de: {model_b_root}")
        sys.exit(1)
    print(f"Modelo A .SemanticModel: {a_sem}")
    print(f"Modelo B .SemanticModel: {b_sem}")

    # encontrar definition/tables
    a_def = get_definition_tables_folder(a_sem)
    b_def = get_definition_tables_folder(b_sem)
    if not a_def or not b_def:
        print("ERRO: não encontrei definition/tables ou definition em um dos modelos.")
        print("A verificação esperada é: <model>.SemanticModel/definition/tables/*.tmdl  (ou definition/*.tmdl)")
        sys.exit(1)
    print(f"Modelo A definition: {a_def}")
    print(f"Modelo B definition: {b_def}")

    # listar .tmdl
    a_files = list_tmdl_files(a_def)
    b_files = list_tmdl_files(b_def)
    print(f"TABELAS .tmdl encontradas -> Modelo A: {len(a_files)}, Modelo B: {len(b_files)}")

    # parse all tmdls into dict name->parse_result
    print("Lendo arquivos .tmdl (pode demorar um pouco dependendo do tamanho)...")
    source_parsed = {}
    target_parsed = {}
    for f in a_files:
        parsed = parse_tmdl_file(f)
        source_parsed[parsed["name"]] = parsed
    for f in b_files:
        parsed = parse_tmdl_file(f)
        target_parsed[parsed["name"]] = parsed

    # compare
    print("Comparando modelos...")
    report = compare_models(source_parsed, target_parsed)

    # print summary
    counts = report["counts"]
    print("\n=== RESUMO ===")
    print(f"Tabelas no Modelo A: {counts['source_total']}")
    print(f"Tabelas no Modelo B: {counts['target_total']}\n")
    print(f"✅ Iguais: {counts['identical']}")
    print(f"⚠️ Diferentes: {counts['different']}")
    print(f"➕ Novas no A: {counts['only_in_source']}")
    print(f"➖ Faltando no A: {counts['only_in_target']}\n")

    # details
    print("=== DETALHES DAS DIFERENÇAS ===")
    lists = report["lists"]
    if lists["only_in_source"]:
        print("\nTabelas apenas no Modelo A:")
        for t in lists["only_in_source"]:
            print("  -", t)
    if lists["only_in_target"]:
        print("\nTabelas apenas no Modelo B:")
        for t in lists["only_in_target"]:
            print("  -", t)
    if report["details"]:
        print("\nTabelas diferentes (com diferenças em colunas/measures/text):")
        for t, d in report["details"].items():
            print(f"\n- {t}:")
            if d["cols_only_in_source"]:
                print("    • Colunas só no A:", ", ".join(d["cols_only_in_source"]))
            if d["cols_only_in_target"]:
                print("    • Colunas só no B:", ", ".join(d["cols_only_in_target"]))
            if d["measures_only_in_source"]:
                print("    • Medidas só no A:", ", ".join(d["measures_only_in_source"]))
            if d["measures_only_in_target"]:
                print("    • Medidas só no B:", ", ".join(d["measures_only_in_target"]))
            if d["textual_diff_snippet"]:
                print("    • Trecho textual (diff) disponível — use mostrar diff completo separadamente se precisar.")
    print("\nFim da comparação.")

if __name__ == "__main__":
    main()
