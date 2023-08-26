<div align="center">
  <a href="https://github.com/jeffreytse/zsh-vi-mode"> TODO
    <img alt="vi-mode →~ zsh" src="https://user-images.githubusercontent.com/9413601/103399068-46bfcb80-4b7a-11eb-8741-86cff3d85a69.png" width="600"> TODO
  </a>
  <p> 💻 A time and task management system for the terminal enthusiast! </p>

  <br> <h1>⚒️ TTM ⚒️</h1>

</div>



<h4 align="center">
  <a href="https://www.zsh.org/" target="_blank"><code>ZSH</code></a> plugin for Agnosticism.
</h4>

<p align="center">

  <a href="https://github.com/sponsors/jeffreytse">
    <img src="https://img.shields.io/static/v1?label=sponsor&message=%E2%9D%A4&logo=GitHub&link=&color=greygreen"
      alt="Donate (GitHub Sponsor)" />
  </a>

  <a href="https://github.com/jeffreytse/zsh-vi-mode/releases">
    <img src="https://img.shields.io/github/v/release/jeffreytse/zsh-vi-mode?color=brightgreen"
      alt="Release Version" />
  </a>

  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-brightgreen.svg"
      alt="License: MIT" />
  </a>

  <a href="https://liberapay.com/jeffreytse">
    <img src="http://img.shields.io/liberapay/goal/jeffreytse.svg?logo=liberapay"
      alt="Donate (Liberapay)" />
  </a>

  <a href="https://patreon.com/jeffreytse">
    <img src="https://img.shields.io/badge/support-patreon-F96854.svg?style=flat-square"
      alt="Donate (Patreon)" />
  </a>

  <a href="https://ko-fi.com/jeffreytse">
    <img height="20" src="https://www.ko-fi.com/img/githubbutton_sm.svg"
      alt="Donate (Ko-fi)" />
  </a>

</p>

<div align="center">
  <h4>
    <a href="#-features">Features</a> |
    <a href="#%EF%B8%8F-installation">Install</a> |
    <a href="#-usage">Usage</a> |
    <a href="#-credits">Credits</a> |
    <a href="#-license">License</a>
  </h4>
</div>

<div align="center">
  <sub>Built with ❤︎ by TODO
  <a href="https://jeffreytse.net">jeffreytse</a> and
  <a href="https://github.com/jeffreytse/zsh-vi-mode/graphs/contributors">contributors </a>
</div>
<br>

<img alt="TTM Demo" src="https://user-images.githubusercontent.com/9413601/105746868-f3734a00-5f7a-11eb-8db5-22fcf50a171b.gif" /> TODO

## 🤔 Why TTM?

TODO


## ✨ Features

- Built as a docker container for reproducible builds and very easy installation.
- Docker image mounts on time and task data outside the container which can be git version controlled
- Integration of various time and task management linux tools as well as vim and tmux for context switching.
- Builds on Vit, a user interface for Taskwarrior, a terminal task management database
  - Allows for Subtasks and note integration for each task. 
  - Integrates Taskwarrior with Calendar events with Calcure and a React google calendar like webapp
  - Integrates with Timetrap for starting and stopping tasks which gives a report on time spent
  - Creates reporting to see how time is broken down by the task, subtask, time code, and project
  - Uses an algorithm to convert order priority calendar events of known time intervals to have known start times
  - Comes with a preprocessor script for easier and generalizable TaskWarrior configuration
- Enables custom vim and tmux configuration for quick navigation, search, and note taking
- Enables custom zsh plugin configuration for quick access to history and sytax highlighting and vim-mode terminal editing
- Comes with Vim macros for color and syntax highlighting of calcure event csv file which updates the react calendar app very quickly
- Comes with Vim commands for creating note entries and note logs with standardized date codes


- 🌟 Pure Zsh's script without any third-party dependencies.
- 🎉 Better experience with the near-native vi(vim) mode.
- ⌛ Lower delay and better response (Mode switching speed, etc.).
- ✏️  Mode indication with different cursor styles.
- 🧮 Cursor movement (Navigation).
- 📝 Insert & Replace (Insert mode).
- 💡 Text Objects (A word, inner word, etc.).
- 🔎 Searching history.
- ❇️  Undo, Redo, Cut, Copy, Paste, and Delete.
- 🪐 Better surrounds functionality (Add, Replace, Delete, Move Around, and Highlight).
- 🧽 Switch keywords (Increase/Decrease Number, Boolean, Weekday, Month, etc.).
- ⚙️  Better functionality in command mode (**In progress**).
- 🪀 Repeating command such as `10p` and `4fa` (**In progress**).
- 📒 System clipboard (**In progress**).

## 💼 Requirements TODO

Docker

## 🛠️ Installation TODO

TODO

## Packaging Status

[![Packaging status](https://repology.org/badge/vertical-allrepos/zsh-vi-mode.svg)](https://repology.org/project/zsh-vi-mode/versions)

## 📚 Usage

TODO

## 🎉 Credits

- [Zsh](https://www.zsh.org/) - A powerful shell that operates as both an interactive shell and as a scripting language interpreter.
- [Oh-My-Zsh](https://github.com/ohmyzsh/ohmyzsh) - A delightful, open source, community-driven framework for managing your ZSH configuration.
- [vim-surround](https://github.com/tpope/vim-surround) - A vim plugin that all about "surroundings": parentheses, brackets, quotes, XML tags, and more.
- [vim-sandwich](https://github.com/machakann/vim-sandwich) - A set of operator and textobject plugins to add/delete/replace surroundings of a sandwiched textobject.

## 🔫 Contributing

Issues and Pull Requests are greatly appreciated. If you've never contributed to an open source project before I'm more than happy to walk you through how to create a pull request.

You can start by [opening an issue](https://github.com/jeffreytse/zsh-vi-mode/issues/new) describing the problem that you're looking to resolve and we'll go from there.

## 🌈 License

This theme is licensed under the [MIT license](https://opensource.org/licenses/mit-license.php) © Jeffrey Tse.
