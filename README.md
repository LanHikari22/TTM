<div align="center">
  <pre>
  ████████╗████████╗███╗░░░███╗
  ╚══██╔══╝╚══██╔══╝████╗░████║
  ░░░██║░░░░░░██║░░░██╔████╔██║
  ░░░██║░░░░░░██║░░░██║╚██╔╝██║
  ░░░██║░░░░░░██║░░░██║░╚═╝░██║
  ░░░╚═╝░░░░░░╚═╝░░░╚═╝░░░░░╚═╝
  </pre>
  <p>An integrated environment for time and task management over docker</p>
</div>

<!-- <p align="center">

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

</p> -->

<div align="center">
  <h4>
    <a href="#-whyttm">Why TTM?</a> |
    <a href="#-features">Features</a> |
    <a href="#%EF%B8%8F-installation">Install</a> |
    <a href="#-usage">Usage</a> |
    <a href="#-future">Future</a> |
    <a href="#-credits">Credits</a> |
    <a href="#-license">License</a>
  </h4>
</div>

<div align="center">
  <sub>Built with ❤︎ by Mohammed Alzakariya
  <!-- <a href="https://jeffreytse.net">jeffreytse</a> and
  <a href="https://github.com/jeffreytse/zsh-vi-mode/graphs/contributors">contributors </a> -->
</div>
<br>

<!-- <img alt="TTM Demo" src="https://user-images.githubusercontent.com/9413602/105746868-f3734a00-5f7a-11eb-8db5-22fcf50a171b.gif" /> TODO -->

## 🤔 Why TTM?

Linux offers many powerful tools for time and task management and note taking. This includes 
taskwarrior and TUI front ends for it such as vit. It includes tmux and vim which can be extended
for quick context switching, searching and recording of data to keep our attention focused. 

Unfortunately, setting up the right environment takes a lot of work and is not easily reproducible
across systems. TTM Offers a fully integrated solution working out of the box with Docker. It
includes customizations to tmux, vim, and taskwarrior to enhance user experience and navigation.

Taskwarrior by default needs a lot of configurations which can also be redundant. TTM configures
all of this off the bat and offers a subtasks feature and integration between taskwarrior and a
calendar react app running out of the box. It also offers note taking capabilities with vim that
can easily track refernce with tasks and the calendar.

So in simple words, use TTM to effectively manage your time over the terminal while leveraging
web services to give intuitive analytics and reports. This can be run over a server and accessed
from anywhere. 


## ✨ Features

- Built as a docker container for reproducible builds and very easy installation.
- Docker image mounts on time and task data outside the container which can be git version controlled

- Integration of various time and task management linux tools as well as vim and tmux for context switching.
  <img src="https://cdn.discordapp.com/attachments/1148294149284573235/1148419701970575440/230904-W36M-gif2.gif" />

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

- A csv file controls the placement of events in the graphical web interface. It also has vim color syntax that can be
  toggled with a macro to a given day to distinguish planned (yellow), completed (cyan), and pending events (white/blue).
  <img src="https://cdn.discordapp.com/attachments/1148294149284573235/1148405695943802900/image.png" />
  <img src="https://cdn.discordapp.com/attachments/1148294149284573235/1148405977712951366/image.png" />

- Comes with Vim commands for creating note entries and note logs with standardized date codes
<img src="https://cdn.discordapp.com/attachments/1148294149284573235/1148403850999513108/image.png" />

- Ability to timeblock floating events that shift with time according to rules
- Treemap and heatmap Visualizations that link the concrete events completed to their tracked task and project structure
<img src="https://cdn.discordapp.com/attachments/1148294149284573235/1148408886756393000/230904-W36M-gif1.gif" />

## 💼 Requirements TODO

Docker

## 🛠️ Installation TODO

Simply install the docker image and run it.

## 📚 Usage

TODO

## 🌱 Future
- Implement syncronization with popular calendar and TODO list apps.
- Implement a rule-based reminder system for events.
- Implement more analytics and seamless event refitting for liquid timeboxing.

## 🎉 Credits

- https://github.com/jeffreytse for the README visual style.

## 🔫 Contributing

Contributions and ideas are always welcome! Feel free to raise a ticket. This is currently early
release and there a lot of features to be added.

## 🌈 License

This theme is licensed under the [MIT license](https://opensource.org/licenses/mit-license.php) © Mohammed Alzakariya.