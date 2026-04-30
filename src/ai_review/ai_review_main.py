from chunk_handler import chunk_pdfs
from analysis_handler import analyze_chunks
from json_compiler import compile_jsons

def main():
    
    chunk_pdfs()
    
    analyze_chunks()
    
    compile_jsons()
    
    return