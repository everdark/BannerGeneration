"""Entrypoint of the Gradio app."""

import os

import gradio as gr

import constants as C
from blocks import (
    ui_about_tab,
    ui_demo_bannertemplateconfig_tab,
    ui_demo_tab_assetcreation,
    ui_demo_tab_assetlibrary,
    ui_demo_tab_bannergen,
)
from config import settings
from utils.firestore import cleanup_document_store, init_document_store
from utils.io import makedir_if_not_exist

for d in [
    os.path.join(settings.local_artefacts_dir, settings.local_actor_dirname),
    os.path.join(settings.local_artefacts_dir, settings.local_actor_processed_dirname),
    os.path.join(settings.local_artefacts_dir, settings.local_banner_dirname),
]:
    makedir_if_not_exist(d)

if settings.is_init_backend:
    cleanup_document_store()
    init_document_store()

os.environ["U2NET_HOME"] = settings.u2net_home

tabs = [
    (ui_about_tab, C.BlockName.ABOUT),
    (ui_demo_tab_assetlibrary, C.BlockName.IMAGE),
    (ui_demo_tab_assetcreation, C.BlockName.CREATE),
    (ui_demo_bannertemplateconfig_tab, C.BlockName.TEMPLATE),
    (ui_demo_tab_bannergen, C.BlockName.BANNER),
]
blocks, tab_names = zip(*tabs)

if __name__ == "__main__":
    demo = gr.TabbedInterface(
        interface_list=blocks, tab_names=tab_names, theme=gr.themes.Default()
    )
    demo.launch(debug=True)
