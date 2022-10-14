
# Retroarch Launcher
## script.akl.retroarchlauncher
| Release | Status |
|----|----|
| Stable | [![Build Status](https://dev.azure.com/jnpro/AKL/_apis/build/status/script.akl.retroarchlauncher?branchName=main)](https://dev.azure.com/jnpro/AKL/_build/latest?definitionId=7&branchName=main)|
| Unstable | [![Build Status](https://dev.azure.com/jnpro/AKL/_apis/build/status/script.akl.retroarchlauncher?branchName=dev)](https://dev.azure.com/jnpro/AKL/_build/latest?definitionId=7&branchName=dev) |

Retroarch Launcher for AKL

The Retroarch launcher depends on an Retroarch instance to be able to launch the scanned ROM files.
Get your copy from the [Retroarch website](http://www.retroarch.com/).

## Creating a Retroarch Launcher

When you create a Retroarch launcher AKL will try to find all Retroarch configuration files available
in the application folder. Either select one of the found configuration files or specify the path to
the configuration file manually. Once given AKL will automatically load the configuration file and
use the configured cores and infos folder to present the list of available cores.

When you select the desired core AKL will also apply the default ROM extensions of the core and use
the systemname and manufactorer as default information for the launcher. All of this you can change
in the following steps after selecting the core.

You can also add extra launch arguments, but take note that the default launching arguments will be
already added by the launcher itself. The used arguments are for selecting the correct core instance,
the correct configuration file and ofcourse the actual ROM file. 

Details about the CLI arguments can be found [here](https://docs.libretro.com/guides/cli-intro/).

## On Android

The default paths for Retroarch cores and info files under Android are only scannable when the OS
is rooted. When running on a non-rooted Android box the best option is to open up Retroarch and
configure paths for the cores and infos that are actually accessible. 
Don't forget to update/download the cores and info file after changing the paths.

### Kodi forum thread ###

More information and discussion about AKL can be found in the [Advanced Kodi Launcher thread] 
in the Kodi forum.

[Advanced Kodi Launcher thread]: https://forum.kodi.tv/showthread.php?tid=366351

### Documentation ###

Read more about AKL on the main plugin's [ReadMe](https://github.com/chrisism/plugin.program.akl/blob/master/README.md) page.

### Settings ###
The Retroarch plugin experience can be optimized using the addon settings. Depending on the access level (basic,standard..etc) you can be able to see and change the following settings:

| Group | Setting | Description |
| --- | --- | --- |
| Paths | Retroarch application path | Default path to the Retroarch executable. |
| Advanced | Action on Kodi playing media | Indicate what AKL needs to do with Kodi when the addon wants to launch a ROM and media is currently playing. Default action is to stop the media. |
| Advanced | After/before launch delay (ms) | Amount of milliseconds to wait before executing/launching the ROM. |
| Advanced | Suspend/resume Kodi audio engine | Will suspend the Kodi audio engine (like menu sounds) while the ROM is launched. |
| Advanced | Suspend/resume Kodi screensaver | Temporary disables the screensaver in Kodi while launching the ROM. |
| Advanced | Suspend/resume Kodi joystick engine | Temporary disables the joystick engine in Kodi while launching the ROM so that it will not intervene with running the ROM. |
| Advanced | Escape $rom$ quotes | Will escape the ' (quotes) symbols in the ROM file path. This can mess up execution arguments. | 
| Advanced | Disable LIRC | Applicable on Linux only. Will disable the LIRC (infrared connector) in Kodi so it will not interact with the launched ROM. |
| Advanced | Close file descriptor | Windows only. Closes the file descriptor. Use in case processes get locked. | 
| Advanced | CD into application dir | Windows only. Will execute the application with the application directory as the current working/active directory. |
| Advanced | Log level | Verbosity level of logging. |