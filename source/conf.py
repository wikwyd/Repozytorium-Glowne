# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Sprawozdanie-z-laboratoriów'
copyright = '2026, Olaf Chomicki, Konrad Machowski, Wiktor Wydrzyński'
author = 'Olaf Chomicki, Konrad Machowski, Wiktor Wydrzyński'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

# -- Options for LaTeX output ------------------------------------------------
# Optymalizacja generowania PDF - eliminacja pustych stron między rozdziałami
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '11pt',
    'fncychap': '\\usepackage[Bjarne]{fncychap}',
    'extraclassoptions': 'openany,oneside',  # KLUCZOWE: wyłącza openright i twoside
    'preamble': r'''
\usepackage{babel}
\usepackage{graphicx}
\usepackage{hyperref}
\setcounter{tocdepth}{2}
\raggedbottom

% Zmniejszenie przestrzeni przed nagłówkami
\setlength{\parskip}{0pt plus 1pt}
\setlength{\parindent}{0pt}

% Zwiększenie wysokości headera
\setlength{\headheight}{14.49998pt}
''',
    'sphinxsetup': 'hmargin={0.7in,0.7in}, vmargin={0.7in,0.7in}, verbatimwithframe=false',
}

latex_documents = [
    ('index', 'sprawozdanie-z-laboratoriow.tex', 'Sprawozdanie z Laboratorium: Bazy Danych', 
     'Konrad Machowski', 'manual'),
]

latex_show_urls = 'footnote'
latex_show_pagerefs = False
latex_max_embed_pages = 0
