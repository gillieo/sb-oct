# Diagrams

Three views of the `second_brain` package: how the code is wired together,
how the program is started, and what a user typically does with it.

## 1. Package overview

Every source file, its functions, and what imports what. Solid arrows are
imports or calls that happen at runtime; the dashed arrow marks code that
exists but is not connected to the CLI.

```mermaid
flowchart LR
    subgraph start["Entry points"]
        script["console script<br/>second_brain"]
        mainpy["__main__.py"]
    end

    subgraph cli_group["CLI layer: cli.py"]
        cli_fn["cli()<br/>click group"]
        new_fn["new()"]
        list_fn["list_notes()"]
        show_fn["show()"]
    end

    subgraph notes_group["Business logic: notes.py"]
        notes_dir["notes_dir()"]
        create_note["create_note()"]
        split_tb["split_title_body()"]
        clean_block["_clean_block()"]
        build_path["build_note_path()"]
        slugify["slugify()"]
        list_files["list_note_files()"]
        read_note["read_note()"]
    end

    subgraph log_group["Logging: app.py"]
        configure["configure_logging()"]
        stderr_fmt["stderr_format()"]
        levels["LEVEL_SHORT_NAMES"]
        app_main["main()"]
    end

    subgraph ext["Third-party libraries"]
        click_lib["click"]
        loguru_lib["loguru"]
    end

    subgraph std["Standard library"]
        os_lib["os, pathlib"]
        text_lib["re, unicodedata"]
        time_lib["datetime"]
    end

    script -->|"cli:cli"| cli_fn
    mainpy -->|"imports cli"| cli_fn

    cli_fn -->|"every run"| configure
    cli_fn --> new_fn
    cli_fn --> list_fn
    cli_fn --> show_fn

    new_fn --> notes_dir
    new_fn --> create_note
    list_fn --> notes_dir
    list_fn --> list_files
    show_fn --> notes_dir
    show_fn --> list_files
    show_fn --> read_note

    create_note --> split_tb
    create_note --> build_path
    split_tb --> clean_block
    build_path --> slugify

    configure --> stderr_fmt
    stderr_fmt --> levels
    app_main --> configure
    app_main -.->|"not called by the CLI"| cli_fn

    cli_group -->|"decorators, echo"| click_lib
    cli_group -->|"logger"| loguru_lib
    log_group -->|"sinks"| loguru_lib
    notes_dir --> os_lib
    list_files --> os_lib
    slugify --> text_lib
    create_note --> time_lib
```

## 2. Entry points and arguments

The ways to start the program, the command and arguments each one accepts, and
what runs behind them.

```mermaid
flowchart LR
    subgraph launch["How to start it"]
        a1["uv run second_brain ..."]
        a2["uv run python -m second_brain ..."]
        a3["uv run --env-file .env second_brain ..."]
    end

    subgraph env["Environment variables"]
        e1["SECOND_BRAIN_DIR<br/>default ~/second_brain/"]
        e2["LOG_LEVEL<br/>default INFO"]
        e3["LOG_FILE<br/>default app.log"]
    end

    group["cli group<br/>--help"]
    logging["configure_logging()<br/>stderr + log file"]

    subgraph new_cmd["new TITLE"]
        n_args["TITLE: required<br/>--body or -b: optional<br/>--body - reads stdin"]
        n1["read stdin if body is -"]
        n2["notes_dir()"]
        n3["create_note()"]
        n4["print path to stdout"]
    end

    subgraph list_cmd["list"]
        l_args["no arguments"]
        l1["notes_dir()"]
        l2["list_note_files()<br/>newest first"]
        l3["print numbered list"]
    end

    subgraph show_cmd["show NUMBER"]
        s_args["NUMBER: required integer<br/>from the list output"]
        s1["notes_dir()"]
        s2["list_note_files()"]
        s3["read_note()"]
        s4["print markdown to stdout"]
    end

    subgraph other["Other entry points"]
        o1["scripts/serve_docs.py<br/>runs mkdocs serve"]
        o2["app.main()<br/>logs a greeting, unused by CLI"]
    end

    a1 --> group
    a2 --> group
    a3 --> group
    group --> logging
    e2 --> logging
    e3 --> logging

    group --> n_args
    group --> l_args
    group --> s_args

    n_args --> n1 --> n2 --> n3 --> n4
    l_args --> l1 --> l2 --> l3
    s_args --> s1 --> s2 --> s3 --> s4

    e1 --> n2
    e1 --> l1
    e1 --> s1
```

## 3. Example user flow

A typical session: capture a note, find it again, and read it. Error
branches show what happens when something is missing.

```mermaid
flowchart LR
    start(["Have an idea"]) --> new["second_brain new 'Caching idea'<br/>--body 'Use an LRU.'"]

    new --> saved["Note saved as<br/>YYYY-MM-DD-caching-idea.md"]
    saved --> path["Full path printed"]

    path --> more{"Another<br/>note?"}
    more -->|"yes"| new
    more -->|"no"| list["second_brain list"]

    list --> exists{"Notes folder<br/>exists?"}
    exists -->|"no"| nofolder["Message: folder does not exist<br/>Create a note first"]
    nofolder --> new
    exists -->|"yes"| empty{"Any notes?"}
    empty -->|"no"| nonotes["Message: No notes found"]
    nonotes --> new
    empty -->|"yes"| numbered["Numbered list, newest first<br/>1. 2026-10-25-caching-idea.md"]

    numbered --> show["second_brain show 1"]
    show --> valid{"Number in<br/>range?"}
    valid -->|"no"| err["Error on stderr<br/>exit status 1"]
    err --> list
    valid -->|"yes"| content["Note markdown printed"]

    content --> done(["Idea recalled"])
```
