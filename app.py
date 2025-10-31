# app.py
# Combina Streamlit com a lógica de compare_tmdl.py e merge_tmdl.py

import streamlit as st
import os
import shutil
import re
from pathlib import Path
import sys
import zipfile
import io
import difflib
import tempfile
import copy

# --- Configuração da Página ---
st.set_page_config(
    page_title="Ferramenta de Merge TMDL",
    layout="wide"
)

# --- Funções de Ajuda (Limpeza e ZIP) ---

def cleanup_session_dirs():
    """Remove diretórios temporários de sessões anteriores."""
    if 'temp_base_dir' in st.session_state and st.session_state.temp_base_dir:
        try:
            shutil.rmtree(st.session_state.temp_base_dir)
        except Exception as e:
            print(f"Erro ao limpar diretório antigo: {e}")
    st.session_state.temp_base_dir = None
    st.session_state.temp_model_a_dir = None
    st.session_state.temp_model_b_dir = None
    st.session_state.compare_report = None
    st.session_state.merged_zip_bytes = None
    st.session_state.paths = {}

def unzip_to_temp(zip_file, target_dir):
    """Descompacta um arquivo zip em um diretório alvo."""
    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall(target_dir)
        return True
    except Exception as e:
        st.error(f"Erro ao descompactar {zip_file.name}: {e}")
        return False

def create_zip_from_folder(folder_path):
    """Cria um arquivo zip em memória a partir de uma pasta."""
    zip_buffer = io.BytesIO()
    p = Path(folder_path)
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Itera por todos os arquivos na pasta .SemanticModel
        for file_path in p.rglob('*'):
            if file_path.is_file():
                # O arcname preserva a estrutura de pastas relativas
                # ex: MeuModelo.SemanticModel/definition/tables/MinhaTabela.tmdl
                arcname = file_path.relative_to(p.parent)
                zf.write(file_path, arcname=arcname)
    return zip_buffer.getvalue()

# --- Funções Lógicas (Copiadas de compare_tmdl.py e merge_tmdl.py) ---
# [INÍCIO] Lógica de 'compare_tmdl.py'

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
    files = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() == ".tmdl"]
    return sorted(files, key=lambda x: x.name.lower())

def parse_tmdl_file(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    columns = set()
    measures = set()
    table_pattern = re.compile(r"^\s*table\s+([A-Za-z0-9_ ]+)", re.MULTILINE)
    column_pattern = re.compile(r"^\s*column\s+([A-Za-z0-9_]+)", re.MULTILINE)
    measure_pattern = re.compile(r"^\s*measure\s+'?([^'=]+?)'?\s*=", re.MULTILINE)
    tables = table_pattern.findall(text)
    columns = set(column_pattern.findall(text))
    measures = set(measure_pattern.findall(text))
    name = path.stem
    if tables:
        name = tables[0].strip()
    return {
        "name": name,
        "file": str(path),
        "text": text,
        "columns": columns,
        "measures": measures,
        "raw_json": None
    }

def compare_models(source_files, target_files):
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
        if src["text"] == tgt["text"]:
            identical.append(name)
            continue
        
        src_cols = src["columns"]
        tgt_cols = tgt["columns"]
        src_meas = src["measures"]
        tgt_meas = tgt["measures"]
        cols_only_src = sorted(src_cols - tgt_cols)
        cols_only_tgt = sorted(tgt_cols - src_cols)
        meas_only_src = sorted(src_meas - tgt_meas)
        meas_only_tgt = sorted(tgt_meas - src_meas)
        textual_diff = []

        if not (src_cols or tgt_cols or src_meas or tgt_meas):
            text_diff = difflib.unified_diff(
                src["text"].splitlines(keepends=True),
                tgt["text"].splitlines(keepends=True),
                fromfile=f"{name} (source)",
                tofile=f"{name} (target)",
                lineterm=""
            )
            textual_diff = list(text_diff)[:400]
        
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

    return {
        "counts": {
            "source_total": len(source_names), "target_total": len(target_names),
            "identical": len(identical), "different": len(different),
            "only_in_source": len(only_in_source), "only_in_target": len(only_in_target)
        },
        "lists": {
            "identical": identical, "different": different,
            "only_in_source": only_in_source, "only_in_target": only_in_target
        },
        "details": diffs_details
    }
# [FIM] Lógica de 'compare_tmdl.py'

# --- Funções Lógicas (Copiadas de merge_tmdl.py) ---
# [INÍCIO] Lógica de 'merge_tmdl.py'

def read_tmdl_text(path: Path):
    return path.read_text(encoding="utf-8", errors="ignore")

def remove_lineage_tags(text: str):
    return re.sub(r"^\s*lineageTag:.*?$", "", text, flags=re.MULTILINE)

def remove_variation_blocks(text: str):
    lines = text.splitlines()
    new_lines = []
    skip_mode = False
    base_indent = None
    for line in lines:
        if not skip_mode and re.match(r"^\s*variation\s+\S+", line):
            skip_mode = True
            base_indent = len(line) - len(line.lstrip())
            continue
        if skip_mode:
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent and line.strip() != "":
                skip_mode = False
                new_lines.append(line)
                continue
            continue
        new_lines.append(line)
    return "\n".join(new_lines)

def get_text_before_partition(text: str):
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith("partition "):
            break
        new_lines.append(line)
    return "\n".join(new_lines).rstrip() + "\n"

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

def merge_table(a_text: str, b_text: str):
    a_text = remove_variation_blocks(a_text)  #
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
# [FIM] Lógica de 'merge_tmdl.py'

# --- Inicialização do Session State ---
if 'compare_report' not in st.session_state:
    st.session_state.compare_report = None
if 'temp_base_dir' not in st.session_state:
    st.session_state.temp_base_dir = None
if 'merged_zip_bytes' not in st.session_state:
    st.session_state.merged_zip_bytes = None
if 'paths' not in st.session_state:
    st.session_state.paths = {}


# --- Interface Principal (Streamlit) ---
st.title("Ferramenta de Merge para Modelos Semânticos (TMDL)")

with st.expander("📘 Instruções de Uso", expanded=True):
    st.markdown("""
    Prepare seus modelos
    1.  Exporte dois arquivos `.zip` contendo as pastas do modelo semântaico (.pbip) do Power BI.
    2.  **Modelo A → Fonte** (modelo mais novo)
    3.  **Modelo B → Destino** (modelo base no qual será aplicado o merge)

    Etapas do processo
    1.  Vá até a aba **Comparar** para identificar diferenças entre os modelos.
    2.  Depois, na aba **Mesclar**, una as tabelas novas e atualizadas no Modelo B.

    Resultado
    * Após o merge, você poderá **baixar o novo Modelo B atualizado** em formato `.zip`,
        pronto para ser substituído no seu projeto Power BI.
    
    💡 **Dica:** Use sempre versões limpas exportadas do Power BI para evitar conflitos.
    """)

st.divider()

# --- Upload dos Arquivos ---
col1, col2 = st.columns(2)
with col1:
    model_a_zip = st.file_uploader("1. Modelo A (.zip Fonte / Novo)", type="zip")
with col2:
    model_b_zip = st.file_uploader("2. Modelo B (.zip Destino / Base)", type="zip")

# --- Abas de Ação ---
tab_comparar, tab_mesclar = st.tabs(["Comparar", "Mesclar"])

with tab_comparar:
    st.header("Análise de Diferenças")
    
    if st.button("Comparar Modelos"):
        if model_a_zip and model_b_zip:
            # Limpa diretórios de sessões anteriores
            cleanup_session_dirs()
            
            # Cria um diretório temporário base para esta sessão
            st.session_state.temp_base_dir = tempfile.mkdtemp(prefix="st_tmdl_")
            temp_a_path = Path(st.session_state.temp_base_dir) / "model_a"
            temp_b_path = Path(st.session_state.temp_base_dir) / "model_b"
            os.makedirs(temp_a_path, exist_ok=True)
            os.makedirs(temp_b_path, exist_ok=True)
            
            with st.spinner("Descompactando e comparando modelos..."):
                # Descompactar
                if not (unzip_to_temp(model_a_zip, temp_a_path) and 
                        unzip_to_temp(model_b_zip, temp_b_path)):
                    st.error("Falha ao descompactar um ou ambos os arquivos. Verifique os zips.")
                    cleanup_session_dirs()
                else:
                    # Adaptado do main() de 'compare_tmdl.py'
                    a_sem = find_semantic_model_folder(str(temp_a_path)) #
                    b_sem = find_semantic_model_folder(str(temp_b_path)) #
                    
                    if not a_sem or not b_sem:
                        st.error("ERRO: não encontrei pasta *.SemanticModel dentro de um dos zips.") #
                        cleanup_session_dirs()
                    else:
                        a_def = get_definition_tables_folder(a_sem) #
                        b_def = get_definition_tables_folder(b_sem) #
                        
                        if not a_def or not b_def:
                            st.error("ERRO: não encontrei definition/tables ou definition em um dos modelos.") #
                            cleanup_session_dirs()
                        else:
                            st.session_state.paths = {"a_def": a_def, "b_def": b_def, "b_sem": b_sem}
                            
                            a_files = list_tmdl_files(a_def) #
                            b_files = list_tmdl_files(b_def) #
                            
                            source_parsed = {}
                            target_parsed = {}
                            for f in a_files:
                                parsed = parse_tmdl_file(f) #
                                source_parsed[parsed["name"]] = parsed
                            for f in b_files:
                                parsed = parse_tmdl_file(f) #
                                target_parsed[parsed["name"]] = parsed
                                
                            report = compare_models(source_parsed, target_parsed) #
                            st.session_state.compare_report = report
                            st.success("Comparação concluída!")
        else:
            st.warning("Por favor, faça o upload dos dois arquivos .zip.")

    # Exibe os resultados da comparação
    if st.session_state.compare_report:
        report = st.session_state.compare_report
        counts = report["counts"] #
        lists = report["lists"] #
        
        st.subheader("=== RESUMO ===")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("✅ Iguais", counts['identical']) #
        c2.metric("⚠️ Diferentes", counts['different']) #
        c3.metric("➕ Novas no A", counts['only_in_source']) #
        c4.metric("➖ Faltando no A", counts['only_in_target']) #

        with st.expander("=== DETALHES DAS DIFERENÇAS ==="):
            if lists["only_in_source"]: #
                st.write("**Tabelas apenas no Modelo A (serão ADICIONADAS):**")
                st.json(lists["only_in_source"])
            if lists["different"]: #
                st.write("**Tabelas diferentes (serão ATUALIZADAS):**")
                st.json(lists["different"])
            if lists["only_in_target"]: #
                st.write("**Tabelas apenas no Modelo B (serão MANTIDAS):**")
                st.json(lists["only_in_target"])
        
        st.info("Vá para a aba 'Mesclar' para aplicar as mudanças.")


with tab_mesclar:
    st.header("Mesclar Modelos")
    
    if not st.session_state.compare_report:
        st.info("Por favor, execute a comparação na aba 'Comparar' primeiro.")
    else:
        st.warning("⚠️ **Atenção:** O merge sobrescreverá tabelas modificadas e "
                   "adicionará tabelas novas. O Modelo B original será preservado "
                   "no zip, mas esta ação é baseada na lógica dos scripts fornecidos.")

        if st.button("Realizar Merge e Gerar Arquivo"):
            with st.spinner("Realizando o merge... (Adaptado de 'merge_tmdl.py')"):
                try:
                    # Adaptado do main() de 'merge_tmdl.py'
                    a_def = st.session_state.paths['a_def']
                    b_def = st.session_state.paths['b_def']
                    
                    a_files = list_tmdl_files(a_def) #
                    b_files = list_tmdl_files(b_def) #
                    
                    b_map = {f.stem: f for f in b_files} #
                    a_map = {f.stem: f for f in a_files} #
                    
                    novas = []
                    atualizadas = []
                    
                    for name, a_path in a_map.items():
                        if name.startswith("LocalDateTable"): #
                            continue
                        
                        a_text = read_tmdl_text(a_path) #
                        
                        if name in b_map:
                            # Atualiza tabela existente
                            b_path = b_map[name]
                            b_text = read_tmdl_text(b_path) #
                            merged = merge_table(a_text, b_text) #
                            b_path.write_text(merged, encoding="utf-8") #
                            atualizadas.append(name)
                        else:
                            # Adiciona tabela nova
                            destino = Path(b_def) / a_path.name #
                            cleaned = remove_variation_blocks(a_text) #
                            cleaned = remove_lineage_tags(cleaned) #
                            destino.write_text(cleaned, encoding="utf-8") #
                            novas.append(name)
                    
                    st.success("Merge concluído no diretório temporário! Gerando arquivo .zip...")
                    
                    # Cria o zip a partir da pasta .SemanticModel modificada
                    b_sem_path = st.session_state.paths['b_sem']
                    zip_bytes = create_zip_from_folder(Path(b_sem_path))
                    st.session_state.merged_zip_bytes = zip_bytes
                    
                    # Exibe o resultado do merge
                    st.subheader("=== RESULTADO DO MERGE ===")
                    st.write(f"🆕 **Tabelas novas copiadas:** {len(novas)}")
                    if novas:
                        st.json(novas)
                    st.write(f"🔁 **Tabelas atualizadas:** {len(atualizadas)}")
                    if atualizadas:
                        st.json(atualizadas)

                except Exception as e:
                    st.error(f"Ocorreu um erro durante o merge: {e}")
                    st.session_state.merged_zip_bytes = None

    # Botão de Download (só aparece se o merge foi concluído)
    if st.session_state.merged_zip_bytes:
        st.divider()
        st.download_button(
            label="Baixar Modelo B Mesclado (.zip)",
            data=st.session_state.merged_zip_bytes,
            file_name="Modelo_B_Mesclado.zip",
            mime="application/zip"
        )