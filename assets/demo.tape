# VHS tape for the README demo — render with `vhs assets/demo.tape`
# (https://github.com/charmbracelet/vhs). Produces assets/demo.gif.

Output assets/demo.gif

Require uv-upsync

Set Shell "bash"
Set FontSize 18
Set Width 1100
Set Height 620
Set Padding 24
Set Theme "Dracula"
Set TypingSpeed 70ms

Type "uv-upsync --project assets/demo --dry-run"
Sleep 800ms
Enter
Sleep 5s
