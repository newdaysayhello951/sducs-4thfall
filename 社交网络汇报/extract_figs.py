import fitz, os

os.makedirs('ppt_assets', exist_ok=True)
doc = fitz.open('2026.acl-long.1648(1).pdf')
print('Total pages:', len(doc))

# Render key pages at 2x DPI for crisp figures
# Page indices (0-based): 0=Fig1, 2=Fig2, 4=Fig3+Fig4, 5=Fig5
targets = {
    0: 'fig1_example.png',
    2: 'fig2_pipeline.png',
    4: 'fig3_failure_fig4_rmd.png',
    5: 'fig5_mans.png',
}
for idx, name in targets.items():
    page = doc[idx]
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
    out = f'ppt_assets/{name}'
    pix.save(out)
    print(f'Saved {out} ({pix.width}x{pix.height})')
doc.close()
print('Done.')
