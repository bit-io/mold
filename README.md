# mold

Biblioteka TUI dla **HackerScript** (bit.io), mocno wzorowana na [ratatui](https://ratatui.rs):
`Buffer`/`Cell`, `Rect` + `Layout`/`Constraint`, `Style`, `Span`/`Line`/`Text`, `Terminal` z rysowaniem
różnicowym oraz widgety `Block`, `Paragraph`, `ListWidget`, `Table`, `Gauge`, `Tabs`, `Sparkline`,
`BarChart`, `Scrollbar`, `Clear`, `Canvas` (Braille/blok/kropki), `Chart` (linie i punkty, osie, legenda) oraz `Calendar`. Cały kod to `.hcs`; jedyny natywny kawałek (`lib/backend.hcs`: tryb raw,
rozmiar terminala, zdarzenia, Unicode) to `native {Rust}` **wyłącznie na `std`** — zero crate'ów.

```
bit install mold
```

```
get <bit:mold>

fun main() [
    let term = terminal_init()
    let running = true
    while running [
        let area = terminal_begin(term)            !! czysci bufor, obsluguje resize
        let blk = block_bordered()
        block_set_title(blk, " mold ")
        let p = paragraph_from_str("Hello, mold!")
        paragraph_set_block(p, blk)
        render_paragraph(term.buffer, p, area)     !! widgety rysuja do term.buffer
        terminal_end(term)                         !! wysyla tylko zmienione komorki

        let ev = event_poll(200)
        if event_is_key(ev, "q") [
            running = false
        ]
    ]
    terminal_restore(term)                         !! ZAWSZE przywroc terminal
]
```

## Różnice względem ratatui

HackerScript nie ma closures, traitów, builderów-łańcuchów ani operatorów bitowych, więc:

| ratatui | mold |
|---|---|
| `terminal.draw(\|f\| ...)` | pętla: `terminal_begin` → `render_*(term.buffer, ...)` → `terminal_end` |
| `Block::bordered().title("x")` | `let b = block_bordered()` + `block_set_title(b, "x")` (settery mutują) |
| `Constraint::Length(3)` | `constraint_length(3)` (`_percentage`, `_ratio`, `_min`, `_max`, `_fill`) |
| `Layout::vertical([..]).split(area)` | `layout_vertical([..], area)`; z marginesem/odstępem: `layout_split(area, horizontal, cs, margin, spacing)` |
| `Color::Red`, `Modifier::BOLD` | `COLOR_RED`, `MOD_BOLD` (Int); `color_rgb(r,g,b)`, `color_indexed(n)` |
| `Style::default().fg(..).bold()` | `style_of(fg, bg, mods)` albo `style_bold(style_fg(style_new(), COLOR_RED))` |
| `List` | `ListWidget` (`List` to wbudowany typ HackerScript) |
| `Style::default().fg(..)` zagnieżdżone | buildery `*_with_*` zwracają kopię: `block_with_border_type(block_with_title(block_bordered(), "x"), BORDER_ROUNDED)`; skrót `block_titled("x")` |
| `ListState`/`TableState` | `list_state_*` / `table_state_*` (`next`, `previous`, `select`) |

Kolory: `0` = dziedzicz, `1` = reset, `2..17` = ANSI. Modyfikatory to flagi (potęgi dwójki): `mods_has/mods_add`.

## Moduły (`lib/`)

`style` · `geometry` (Rect, Constraint, Layout) · `text` (Span/Line/Text) · `buffer` · `terminal` (Terminal + zdarzenia) ·
`widget_block` (Block, Clear) · `widget_paragraph` · `widget_list` (ListWidget, Table) · `widget_misc` (Gauge, Tabs,
Sparkline, BarChart, Scrollbar) · `widget_canvas` (Canvas, Chart) · `widget_calendar` · `builders` (`*_with_*`) · `backend` (natywna warstwa). `get <bit:mold>` ładuje całość,
`get <bit:mold::widget_list>` pojedynczy moduł.

## Zdarzenia

`event_poll(timeout_ms) -> Event` (`kind`, `code`, `mods`, `x`, `y`). `kind`: `key`, `resize`, `none` (timeout),
`mouse_down|up|drag|move|scroll`, `eof`. Klawisze: znak (`"a"`, `"ż"`) lub nazwa (`Enter`, `Esc`, `Tab`, `BackTab`,
`Up`, `PageDown`, `F1`…). Modyfikatory: `KEY_SHIFT`=1, `KEY_CTRL`=2, `KEY_ALT`=4. Mysz włącza `terminal_init_mouse()`.
Tryb raw wyłącza `ISIG`, więc Ctrl+C przychodzi jako zdarzenie (`event_is_ctrl(ev, "c")`); panic-hook przywraca terminal.

## Przykłady i testy

* `examples/hello` — minimum, `examples/dashboard` — wszystkie widgety, mysz, popup, resize.
* `examples/render-test` — asercje na `Buffer` bez terminala (`bit test`).
* `tests/pty_run.py` — uruchamia program na pseudoterminalu (klawisze, resize) i wypisuje ekran.

## Canvas, Chart, Calendar

```
let cv = canvas_new(24, 8, MARKER_BRAILLE, 0.0, 10.0, 0.0, 10.0)   !! szer/wys w komorkach, zakresy osi
canvas_line(cv, 0.0, 0.0, 10.0, 10.0, COLOR_YELLOW)                !! tez canvas_point/rect/circle/label
render_canvas(term.buffer, cv, area)

let xa = axis_new(0.0, 12.0)
axis_auto_labels(xa, 4, 0)
let ch = chart_new([dataset_new("sin", xs, ys, COLOR_CYAN, true)], xa, axis_new(-1.0, 1.0))
render_chart(term.buffer, ch, area)

let cal = calendar_new(2026, 10)     !! polskie nazwy; calendar_set_lang(cal, 1) = angielskie
calendar_add_event(cal, 5, style_of(COLOR_RED, 0, 0))
render_calendar(term.buffer, cal, area)
```

Markery: `MARKER_BRAILLE` (2x4 na komórkę), `MARKER_HALF` (1x2), `MARKER_BLOCK`, `MARKER_DOT`.
Komórki tabeli mogą mieć wiele linii (`"a\nb"` w `row_from_strs`, `row_from_texts`); wysokość wiersza liczy się automatycznie.

## Unicode

Szerokość znaków pochodzi z tabel wygenerowanych z Unicode 15.0 (znaki łączące i formatujące = 0, East Asian
Wide/Fullwidth = 2), a klastry obejmują sekwencje ZWJ, modyfikatory skóry, flagi (para regional indicators),
VS16 i sylaby hangul.

## Ograniczenia (0.2)

Linux/Unix (termios deklarowane przez `extern "C"`). Szerokość jest zgodna z `wcwidth` dla Unicode 15; terminale
potrafią renderować złożone emoji inaczej niż tabela. `ListWidget` zamiast `List` (wbudowany typ), brak closures,
więc zamiast `terminal.draw(|f| ...)` pętla `terminal_begin`/`terminal_end`. Źródła kompilowane i testowane
`hackerc` zbudowanym ze źródeł HackerScript 0.5 (binarka 0.4 nie re-eksportuje `include` przez `get <bit:...>`).
