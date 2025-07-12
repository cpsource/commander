Here's how to install GitHub CLI on a headless Ubuntu box:

**Method 1: Using the official GitHub CLI repository (recommended):**

```bash
# Update package list
sudo apt update

# Install required packages
sudo apt install -y curl gpg

# Add GitHub CLI repository
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

# Update and install
sudo apt update
sudo apt install gh
```

**Method 2: Using snap (simpler but sometimes older version):**

```bash
sudo snap install gh
```

**Method 3: Download binary directly:**

```bash
# Download latest release (check GitHub for current version)
wget https://github.com/cli/cli/releases/download/v2.40.1/gh_2.40.1_linux_amd64.tar.gz

# Extract and install
tar -xzf gh_2.40.1_linux_amd64.tar.gz
sudo cp gh_2.40.1_linux_amd64/bin/gh /usr/local/bin/
```

**After installation, authenticate:**

```bash
# For headless authentication, use a token
gh auth login --with-token < token.txt

# Or use the web-based flow (will give you a code to enter on another device)
gh auth login --web
```

**Verify installation:**

```bash
gh --version
gh auth status
```

Think of it like installing a remote control for your GitHub account - once it's set up, you can manage repositories, create PRs, and handle authentication all from the command line without needing a web browser.

**For the headless authentication**, the `--web` option is usually easiest - it gives you a code that you can enter on any device with a browser to complete the authentication.
