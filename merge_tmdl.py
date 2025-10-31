"""
merge_tmdl.py

Atualiza o Modelo B com base no Modelo A (.tmdl):
- Cria backup completo do modelo B
- Remove em B tudo a partir de 'partition'
- Copia tabelas/medidas de A (ignorando LocalDateTable e variation)
- Remove lineageTag apenas dos arquivos novos (vindos do A)
- Mantém lineageTag das tabelas já existentes
- Respeita indentação e estrutura
"""

import os
import shutil
import re
from pathlib import Path
import sys

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
    return input(f"{prompt}\nCaminho: ").strip()

def find_semantic_model_folder(root_path: str):
    root = Path(root_path)
    if not root.exists():
        return None
    for p in root.rglob("*"):
        if p.is_dir() and p.name.lower().endswith(".semanticmodel"):
            return str(p)
    if root.name.lower().endswith(".semanticmodel") and root.is_dir():
        return str(root)
    return None

def get_definition_tables_folder(semantic_model_folder: str):
    cand1 = Path(semantic_model_folder) / "definition" / "tables"
    cand2 = Path(semantic_model_folder) / "definition"
    if cand1.exists() and cand1.is_dir():
        return str(cand1)
    if cand2.exists() and cand2.is_dir():
        return str(cand2)
    return None

def list_tmdl_files(def_tables_folder: str):
    p = Path(def_tables_folder)
    return sorted([f for f in p.iterdir() if f.is_file() and f.suffix.lower() == ".tmdl"], key=lambda x: x.name.lower())

def read_tmdl_text(path: Path):
    return path.read_text(encoding="utf-8", errors="ignore")

def remove_lineage_tags(text: str):
    """Remove linhas de lineageTag"""
    return re.sub(r"^\s*lineageTag:.*?$", "", text, flags=re.MULTILINE)

def remove_variation_blocks(text: str):
    """
    Remove blocos 'variation ...' inteiros do texto,
    incluindo linhas aninhadas (isDefault, relationship, defaultHierarchy etc.)
    até a próxima linha com indentação igual ou menor.
    """
    lines = text.splitlines()
    new_lines = []
    skip_mode = False
    base_indent = None

    for line in lines:
        # Detecta início do bloco variation
        if not skip_mode and re.match(r"^\s*variation\s+\S+", line):
            skip_mode = True
            base_indent = len(line) - len(line.lstrip())
            continue

        # Se estiver pulando, verifica se a indentação voltou
        if skip_mode:
            indent = len(line) - len(line.lstrip())
            # Sai do bloco quando volta à indentação igual ou menor que a do variation
            if indent <= base_indent and line.strip() != "":
                skip_mode = False
                new_lines.append(line)
            # Caso contrário, ignora as linhas internas
            continue

        new_lines.append(line)

    return "\n".join(new_lines)


def get_text_before_partition(text: str):
    """Retorna o conteúdo até a linha 'partition' (excluindo ela e tudo abaixo)."""
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith("partition "):
            break
        new_lines.append(line)
    return "\n".join(new_lines).rstrip() + "\n"

# helpers: extrair blocos e indentação

def extract_column_blocks(text: str):
    pattern = re.compile(r"(^\s*column\s+'?([^'\r\n]+?)'?\b.*?)(?=\n\s*column\b|\n\s*measure\b|\n\s*partition\b|\Z)", re.DOTALL | re.MULTILINE)
    blocks = {}
    for m in pattern.finditer(text):
        full = m.group(1)
        name = m.group(2).strip()
        blocks[name] = full.rstrip()
    return blocks

def extract_measure_blocks(text: str):
    pattern = re.compile(r"(^\s*measure\s+'?([^'=]+?)'?\s*=.*?)(?=\n\s*measure\b|\n\s*column\b|\n\s*partition\b|\Z)", re.DOTALL | re.MULTILINE)
    blocks = {}
    for m in pattern.finditer(text):
        full = m.group(1)
        name = m.group(2).strip()
        blocks[name] = full.rstrip()
    return blocks

def extract_partition_block(text: str):
    m = re.search(r"(\n?\s*partition\s+[\s\S]*)", text, re.IGNORECASE)
    if m:
        return m.group(1).rstrip()
    return None

def remove_lineage_tags_from_block(block: str):
    return re.sub(r"^\s*lineageTag:.*?$", "", block, flags=re.MULTILINE)

def indent_block(block: str, tab="\t"):
    lines = []
    for line in block.splitlines():
        if line.strip() == "":
            lines.append("")
        else:
            stripped = line.lstrip()
            lines.append(tab + stripped)
    return "\n".join(lines)

def merge_table(a_text: str, b_text: str):
    """
    Mescla: mantém conteúdo do B até antes do partition; 
    adiciona no B apenas as colunas/medidas que existem em A e não em B;
    adiciona a partition inteira do A (removendo lineageTag se houver),
    respeitando a indentação original do A.
    """
    a_text = remove_variation_blocks(a_text)  # <-- remove blocos variation

    a_cols = extract_column_blocks(a_text)
    a_meas = extract_measure_blocks(a_text)
    a_part = extract_partition_block(a_text)

    b_cols = extract_column_blocks(b_text)
    b_meas = extract_measure_blocks(b_text)
    b_before = get_text_before_partition(b_text)

    additions = []

    for col_name, col_block in a_cols.items():
        if col_name not in b_cols:
            clean_block = remove_lineage_tags_from_block(col_block)
            additions.append(clean_block.rstrip())

    for meas_name, meas_block in a_meas.items():
        if meas_name not in b_meas:
            clean_block = remove_lineage_tags_from_block(meas_block)
            additions.append(clean_block.rstrip())

    merged_parts = [b_before.rstrip()]

    if additions:
        merged_parts.append("")
        merged_parts.extend(additions)

    if a_part:
        clean_part = remove_lineage_tags_from_block(a_part)
        merged_parts.append("")
        merged_parts.append(clean_part.rstrip())
    else:
        b_part = extract_partition_block(b_text)
        if b_part:
            merged_parts.append("") 
            merged_parts.append(b_part.rstrip())

    merged = "\n".join(merged_parts).rstrip() + "\n"
    return merged


def backup_folder(src_folder):
    backup_path = Path(src_folder).parent / (Path(src_folder).name + "_backup")
    if backup_path.exists():
        shutil.rmtree(backup_path)
    shutil.copytree(src_folder, backup_path)
    print(f"✅ Backup criado em: {backup_path}")
    return backup_path

def main():
    print("=== Merge de modelos .tmdl ===")
    print("Selecione o Modelo A (fonte):")
    model_a_root = pick_folder_gui("Selecione a pasta raiz do Modelo A (ou digite o caminho)")
    print("Selecione o Modelo B (destino):")
    model_b_root = pick_folder_gui("Selecione a pasta raiz do Modelo B (ou digite o caminho)")

    a_sem = find_semantic_model_folder(model_a_root)
    b_sem = find_semantic_model_folder(model_b_root)
    if not a_sem or not b_sem:
        print("Erro: não foi possível localizar a pasta .SemanticModel.")
        sys.exit(1)

    a_def = get_definition_tables_folder(a_sem)
    b_def = get_definition_tables_folder(b_sem)
    if not a_def or not b_def:
        print("Erro: não encontrei definition/tables em um dos modelos.")
        sys.exit(1)

    backup_folder(b_sem)

    a_files = list_tmdl_files(a_def)
    b_files = list_tmdl_files(b_def)

    b_map = {f.stem: f for f in b_files}
    a_map = {f.stem: f for f in a_files}

    novas = []
    atualizadas = []

    for name, a_path in a_map.items():
        # Ignora tabelas LocalDateTable
        if name.startswith("LocalDateTable"):
            print(f"⏩ Ignorado (LocalDateTable): {name}")
            continue

        a_text = read_tmdl_text(a_path)

        if name in b_map:
            b_path = b_map[name]
            b_text = read_tmdl_text(b_path)
            merged = merge_table(a_text, b_text)
            b_path.write_text(merged, encoding="utf-8")
            atualizadas.append(name)
        else:
            destino = Path(b_def) / a_path.name
            # Remove variation e lineageTag das novas
            cleaned = remove_variation_blocks(a_text)
            cleaned = remove_lineage_tags(cleaned)
            destino.write_text(cleaned, encoding="utf-8")
            novas.append(name)

    print("\n=== RESULTADO ===")
    print(f"🆕 Tabelas novas copiadas: {len(novas)}")
    for n in novas:
        print("   +", n)
    print(f"🔁 Tabelas atualizadas: {len(atualizadas)}")
    for n in atualizadas:
        print("   *", n)
    print("\n✅ Merge concluído com sucesso!")

if __name__ == "__main__":
    main()
