#!/bin/zsh
# Script para compilar o PDF do artigo

set -e  # Parar em erro

cd "$(dirname "$0")/manuscript"

echo "🔨 Compilando artigo LaTeX..."
echo "📄 Arquivo: main.tex"
echo ""

# Primeira passagem (conteúdo)
echo "📌 Passagem 1/2 - Conteúdo e estrutura..."
pdflatex -interaction=nonstopmode -halt-on-error main.tex > /dev/null 2>&1 || {
    echo "❌ Erro na primeira passagem. Vendo detalhes:"
    pdflatex -interaction=nonstopmode main.tex | tail -20
    exit 1
}

# Segunda passagem (referências cruzadas e TOC)
echo "📌 Passagem 2/2 - Referências cruzadas..."
pdflatex -interaction=nonstopmode -halt-on-error main.tex > /dev/null 2>&1 || {
    echo "❌ Erro na segunda passagem. Vendo detalhes:"
    pdflatex -interaction=nonstopmode main.tex | tail -20
    exit 1
}

# Validar PDF gerado
if [ -f "main.pdf" ]; then
    SIZE=$(ls -lh main.pdf | awk '{print $5}')
    PAGES=$(pdfinfo main.pdf 2>/dev/null | grep "Pages:" | awk '{print $2}' || echo "?")

    echo ""
    echo "✅ PDF COMPILADO COM SUCESSO!"
    echo "   📋 Arquivo: main.pdf"
    echo "   📏 Tamanho: $SIZE"
    echo "   📄 Páginas: $PAGES"
    echo ""
    echo "🚀 Pronto para submissão ao IEEE Transactions on Information Forensics and Security!"
else
    echo "❌ Erro: PDF não foi gerado"
    exit 1
fi

# Limpeza de arquivos auxiliares
echo "🧹 Limpando arquivos auxiliares..."
rm -f *.aux *.log *.out *.toc *.bbl *.blg 2>/dev/null

echo "✨ Concluído!"
