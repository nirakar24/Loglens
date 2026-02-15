# LogLens AUR Package

## Building and Publishing to AUR

### Prerequisites

1. **AUR Account**: Register at https://aur.archlinux.org/register
2. **SSH Key**: Add your SSH public key to your AUR account
3. **Tools**: Install `base-devel` and `git`

```bash
sudo pacman -S base-devel git
```

### Initial Setup

1. **Clone AUR Repository** (first time only):

```bash
git clone ssh://aur@aur.archlinux.org/loglens.git loglens-aur
cd loglens-aur
```

2. **Copy Package Files**:

```bash
cp /path/to/loglens/PKGBUILD .
cp /path/to/loglens/.SRCINFO .
```

3. **Update PKGBUILD** with correct URLs and author info:
   - Replace `yourusername` with your GitHub username
   - Update maintainer name and email
   - Update `sha256sums` after creating a release

### Generate .SRCINFO

```bash
makepkg --printsrcinfo > .SRCINFO
```

### Test Build Locally

```bash
# Test the package builds correctly
makepkg -si

# This will:
# - Download sources
# - Build the package
# - Install it on your system
```

### Publish to AUR

```bash
# Add files
git add PKGBUILD .SRCINFO

# Commit
git commit -m "Initial release: loglens 1.0.0"

# Push to AUR
git push origin master
```

## Updating the Package

When releasing a new version:

1. **Update version** in:
   - `PKGBUILD` (pkgver and pkgrel)
   - `setup.py` (version)
   - `pyproject.toml` (version)

2. **Create GitHub release**:
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

3. **Update checksums**:
   ```bash
   # Download the new tarball
   wget https://github.com/yourusername/loglens/archive/v1.0.1.tar.gz
   
   # Generate SHA256
   sha256sum v1.0.1.tar.gz
   
   # Update sha256sums in PKGBUILD
   ```

4. **Regenerate .SRCINFO**:
   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```

5. **Test and publish**:
   ```bash
   makepkg -si  # Test locally
   git add PKGBUILD .SRCINFO
   git commit -m "Update to version 1.0.1"
   git push origin master
   ```

## Installation for Users

Once published on AUR, users can install with an AUR helper:

```bash
# Using yay
yay -S loglens

# Using paru
paru -S loglens

# Manual installation
git clone https://aur.archlinux.org/loglens.git
cd loglens
makepkg -si
```

## Package Commands

After installation, LogLens is available as:

```bash
# Run TUI
logtui

# Or with python
python -m loglens.tui.app
```

## Package Structure

```
loglens-aur/
├── PKGBUILD        # Build script
└── .SRCINFO        # Package metadata (auto-generated)
```

## Maintenance Checklist

- [ ] Update version numbers in PKGBUILD, setup.py, pyproject.toml
- [ ] Create GitHub release and tag
- [ ] Update sha256sums in PKGBUILD
- [ ] Regenerate .SRCINFO
- [ ] Test build locally with `makepkg -si`
- [ ] Commit and push to AUR
- [ ] Test installation from AUR

## Resources

- AUR Submission Guidelines: https://wiki.archlinux.org/title/AUR_submission_guidelines
- PKGBUILD Reference: https://wiki.archlinux.org/title/PKGBUILD
- Creating Packages: https://wiki.archlinux.org/title/Creating_packages
