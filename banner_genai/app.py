import gradio as gr

import constants as C
from blocks import (
    ui_about_tab,
    ui_demo_tab_assetlibrary,
    ui_demo_tab_assetcreation,
    ui_demo_tab_assetpreprocess,
    ui_demo_bannertemplateconfig_tab,
    ui_demo_tab_bannergen,
)
from config import settings
from utils.firestore import cleanup_document_store, init_document_store

if settings.is_init_backend:
    # This will re-create the initial documents saved in Firestore.
    cleanup_document_store()
    init_document_store()

tabs = [
    (ui_about_tab, C.BlockName.ABOUT),
    (ui_demo_tab_assetlibrary, C.BlockName.IMAGE),
    (ui_demo_tab_assetcreation, C.BlockName.CREATE),
    (ui_demo_tab_assetpreprocess, C.BlockName.PREPROCESS),
    (ui_demo_bannertemplateconfig_tab, C.BlockName.TEMPLATE),
    (ui_demo_tab_bannergen, C.BlockName.BANNER),
]
blocks, tab_names = zip(*tabs)

if __name__ == "__main__":
    demo = gr.TabbedInterface(
        interface_list=blocks, tab_names=tab_names, theme=gr.themes.Default()
    )
    demo.launch(debug=True)
