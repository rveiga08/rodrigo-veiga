from nutikacompile import compile_with_nuitka

wholecommand = compile_with_nuitka(
    pyfile=r"C:\Dev_Rodrigo\Python\facial_viewer_intelbras\main.py",
    icon=r'C:\Dev_Rodrigo\Python\facial_viewer_intelbras\icon.png',
    disable_console=True,
    file_version="1.0.0.0",
    onefile=True,
    outputdir="C:\Dev_Rodrigo\Exe",
    addfiles=[
    r"C:\Dev_Rodrigo\Python\facial_viewer_intelbras\error_log.txt",
    r"C:\Dev_Rodrigo\Python\facial_viewer_intelbras\search_error_log.txt",
    ],
    delete_onefile_temp=False,  # creates a permanent cache folder
    needs_admin=True,
    arguments2add="--msvc=14.3 --noinclude-numba-mode=nofollow --jobs=1",
)
