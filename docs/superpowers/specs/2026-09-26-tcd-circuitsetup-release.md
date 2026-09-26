# TCD CircuitSetup Release Spec

- Build every Time Circuits Display PlatformIO environment with `CS_EDITION` from `Software/platformio.ini`.
- During TCD releases, fetch the private `realA10001986/buildac` repository and package the highest-versioned `sound-pack-cs*.zip` as `TCDA.bin`.
- Permit an intentional same-version TCD release refresh so v3.27 can be rebuilt without changing firmware version files or tags.
- Leave the other four prop release jobs unchanged.
- Verify the published firmware identifies the CircuitSetup sound-pack requirement and the published `TCDA.bin` matches BuildAC's latest pack.
