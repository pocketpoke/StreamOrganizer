{ pkgs }:

pkgs.stdenv.mkDerivation {
  pname = "streamorganizer";
  version = "0.1.0";

  src = ./.;

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  buildInputs = [
    pkgs.python3
    pkgs.deno
  ];

  installPhase = ''
    mkdir -p $out/bin

    cp $src/main.py $out/bin/streamorganizer
    chmod +x $out/bin/streamorganizer

    wrapProgram $out/bin/streamorganizer \
      --prefix PATH : ${
        pkgs.lib.makeBinPath [
          pkgs.deno
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
          (pkgs.callPackage /home/user/nix-config/packages/twitchlink.nix { })
        ]
      }
  '';
}
