# Declarative on-the-fly package extension file for AI Agents.
#
# Agents can add packages here directly or via `./bin/nix-add-pkg`:
#   ./bin/nix-add-pkg --system graphviz
#   ./bin/nix-add-pkg --python matplotlib
#   ./bin/nix-add-pkg --oss protobuf
{ pkgs }:
{
  # Extra system CLI binaries added to the default agent shell & verify-env PATH
  systemPackages = with pkgs; [
    # <SYSTEM_PACKAGES>
  ];

  # Extra Python 3 packages added to the main `python3` environment
  pythonPackages = ps: with ps; [
    # <PYTHON_PACKAGES>
  ];

  # Extra packages added to the `oss-polyglot` and `oss-fhs` OSS build/test shells
  ossPackages = with pkgs; [
    # <OSS_PACKAGES>
  ];
}
