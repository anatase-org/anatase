<p align="center">
  <picture>
    <source
      media="(prefers-color-scheme: dark)"
      srcset="cards/base/identity/letterhead-onblack.svg">
    <source
      media="(prefers-color-scheme: light)"
      srcset="cards/base/identity/letterhead-onwhite.svg">
    <img
      src="cards/base/identity/letterhead-onwhite.svg"
      alt="Anatase"
      width="100%"
      max-width="600px">
  </picture>
</p>

# Anatase
Anatase is a second generation immutable image. Rewritten from scratch, it distills three years of learnings from Bazzite to form an image that is more secure, more maintainable, and more stable, while fixing compliance / security issues.

From a user perspective, perhaps at first glance these do not mean much. So, let's boil it down to two axes.

 - **Smaller, more stable, and universal**. There is only one image to cover all handhelds, desktops, laptops, HTPCs, Nvidia*. The ISO is 2x smaller, the image is 2x smaller, and they both install / update much faster without functionality loss**. The ISO preinstalls a small set of (removable) applications, so you can open your PDFs and watch Youtube out of the box.
 - **Compliance, Security, Provenance**. Examples: Steam is not pre-installed (but if you install it, Anatase's gamemode has parity with SteamOS and can offer other launchers in the future), everything is signed using HSM cloud keys (the kernel; which meets Microsoft Secure boot requirements, Flatpaks, and Updates), and the Anatase image as installed only relies on its infrastructure for updates (no GHCR, COPR, Flathub; although included).

*And a placeholder for a second future ARM one.

**Compared to bazzite-deck-nvidia, the closest image with matching functionality, 15/07/2026

The end result is an OS that _feels boring_. You install it and move on with your day. There are games to play, reels to doomscroll, and homework to do. The **optimized drivers are installed already**. Your **PDFs open**, **Spotify works**, **Zoom does not make your laptop prepare for take-off**, **all your controllers work**. Your handheld **power** and **controller settings** are all here too, both on **Desktop** and **Gamemode**. 

## Features

### Plasma Desktop
Anatase ships with KDE Plasma as its main desktop session. It is performant, it _feels_ like Windows, and is progressing rapidly with a core team of competent developers. In addition, the applications in the KDE ecosystem make strong defaults. Anatase preinstalls Ark (Archive Manager), Filelight (Disk Usage Analyzer), Kate (Text Editor), and Okular (Document Viewer), and all of those come from KDE, with styling to match.

![Anatase Plasma desktop](docs/kde1.png)

![Anatase Plasma application launcher](docs/kde2.png)

### Plasma Mobile
Anatase is also the first desktop distribution to deliver Plasma Mobile as a secondary session for tablet-like devices, such as handhelds and tablet-likes (Asus Z13). While Plasma mobile is still in its early days, it already feels great to use, and for its 20MB install size, it delivers a punch and great for use in e.g., Airplanes.

Also shown, the Anatase Browser. A Chromium based browser with **working GPU acceleration**, **support for Spotify & 720p Netflix**, and **a built-in adblocker** that works great and updates with the system**. _Yes, having working GPU acceleration is a big deal in Linux._

![Anatase Browser in Plasma Mobile](docs/mobile1.png)

![Plasma Mobile application launcher](docs/mobile2.png)

**Adblocker is based on UBOLite, a completely offline adblocker, and can be rebuilt on demand if the filter lists become outdated without Chrome Store approval.

### Gamemode
Anatase also ships a Gamemode session that brings in elements from SteamOS as an optional addon to the core desktop experience. Compared to gaming in Plasma Desktop:

 * Gamemode is intuitive to touch
 * It uses less RAM than a Desktop session
 * Brings the game closer to the GPU, with advanced controls for VRR, Framerate, and HDR. 

![Anatase Gamemode performance controls](docs/gamemode.png)

## Contributing

Anatase does not currently accept external contributions. You are welcome to post issues in the issue tracker, with suggestions or bug reports.

## License

Copyright (C) 2026 Antheas Kapenekakis

A copy of the files in this repository is provided to you under the terms of [GNU Affero General Public License v3.0 or later](LICENSE). Exceptions: `.patch` files carry the license of their respective project solely and files with an SDPX license header carry that license solely.

You may reuse the Anatase mark when producing derived images or rehosting unmodified images that are for personal or internal organizational use. Otherwise, [fork](https://github.com/anatase-org/anatase/fork) Anatase and replace the identity card with your type and marks.

**Non-legally binding TLDR:** Anatase is free software and under the terms of AGPLv3, you may freely adapt the software for your or your organization's (internal) needs without publishing your changes. The same applies to the mark. An example of internal use is your IT department installing Anatase on your laptop or you putting it on your son's laptop.

Anatase is not currently at the stage where it can be pre-installed on devices.
