{
  pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-25.11") { },
}:

pkgs.mkShell {
  packages = with pkgs; [
    (python3.withPackages (ps: [
    ]))
    deno

    (pkgs.stdenv.mkDerivation {
      name = "yt-dlp-2026.03.03";
      dontUnpack = true;
      nativeBuildInputs = [ pkgs.autoPatchelfHook ];
      buildInputs = [
        pkgs.zlib
        pkgs.gcc.cc.lib
      ];
      installPhase = ''
        install -Dm755 ${
          pkgs.fetchurl {
            url = "https://github.com/yt-dlp/yt-dlp/releases/download/2026.03.03/yt-dlp_linux";
            hash = "sha256-zHBrlM3hz5LMFV42MqopCrXzgJrajFbCMxEzVQjezfk=";
          }
        } $out/bin/yt-dlp
        chmod +x $out/bin/yt-dlp
      '';
    })
  ];
}
