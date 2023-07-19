# Use latest Ubuntu version as base
FROM ubuntu:latest

# Install necessary packages
RUN apt-get update && apt-get install -y \
  curl \
  openssh-server \
  zsh \
  git \
  vim \
  tmux \
  ripgrep \
  jq \
  nodejs \
  npm \
  ruby-full \
  taskwarrior \
  python3 \
  python3-pip

# Set up SSH
RUN mkdir /var/run/sshd
RUN echo 'root:pass' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Install Node.js
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -

# Setup terminal environment
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Make zsh the default shell
RUN chsh -s $(which zsh)

# Set the timezone
ENV TZ=America/Chicago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Now you can safely install tzdata
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

# Setup place for bins in $PATH
RUN mkdir -p /root/.local/bin
RUN echo 'PATH=/root/.local/bin:$PATH' >> /root/.zshrc
RUN echo 'export TERM=xterm-256color' >> /root/.zshrc
COPY scripts/shellrc /root/.shellrc
RUN echo 'source ~/.shellrc' >> /root/.zshrc
RUN mkdir -p /root/.config/shell
COPY scripts/shell_fzf.sh /root/.config/shell/fzf.sh

# Setup Vim configuration
RUN curl -fLo ~/.vim/autoload/plug.vim --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
COPY scripts/vimrc_plugins /root/.vimrc
RUN vim +PlugInstall +qall
COPY scripts/vimrc /root/.vimrc
COPY scripts/macrobatics /root/.config/macrobatics

# Install tpm for tmux
RUN git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

# Configure Tmux
COPY scripts/tmux.conf /root/.tmux.conf
COPY scripts/tmux_start_sessions.sh /root/tmux_start_sessions.sh
RUN chmod +x /root/tmux_start_sessions.sh
RUN touch /root/.tmux/defaults.conf
RUN tmux start-server \
  && tmux new-session -d \
    && sleep 1 \
      && /root/.tmux/plugins/tpm/scripts/install_plugins.sh \
        && tmux kill-server

# Install Time and task management packages
RUN mkdir /root/src
RUN python3 -m pip install vit tzdata
COPY ttm-tools /root/src/ttm-tools
RUN cd /root/src/ttm-tools && ./release.sh --all -v
#RUN cd /root/.task/taskrc/src && ./replace_system_taskrc.sh && yes | ./context.sh
RUN cd /root/src/ttm-tools/taskrc/src && ./replace_system_taskrc.sh && yes | ./context.sh
RUN mkdir /root/.vit
COPY scripts/vit_config.ini /root/.vit/config.ini
RUN mkdir /root/.vim/colors
COPY scripts/calcure_colors.vim /root/.vim/colors/calcure_colors.vim

# Install timetrap (ruby)
RUN apt-get update && apt-get install -y libsqlite3-dev
RUN gem install timetrap
COPY scripts/timetrap.yml /root/.timetrap.yml

# Install React Calendar
RUN cd /root/src/ && git clone https://github.com/LanHikari22/react-calendar
RUN cd /root/src/react-calendar && git checkout lan-dev && npm install

# Create app directory
#WORKDIR /usr/src/app

# Install app dependencies
#COPY package*.json ./
#RUN npm install

# Bundle app source
#COPY . .

# Expose port
EXPOSE 3000 22

CMD service ssh start && \
  tail -f /dev/null
