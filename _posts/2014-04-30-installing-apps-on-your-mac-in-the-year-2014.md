---
title: "Installing apps on your mac – in the year 2014"
date: 2014-04-30 19:37:02 +0000
permalink: /installing-apps-on-your-mac-in-the-year-2014/
author: "Falko"
categories: ["Aus dem Netz gefischt", "Technik/Software"]
tags: []
wp_id: 1485
---
I never really liked downloading an app, copying it from the dmg to the Applications folder. Unzipping it, moving it… The Mac AppStore is nice, klick-and-install. It also lists you all the apps you ever installed. Which is handy, of you move to a new mac. The same process actually exists with the handy command line tool homebrew cask as well for apps that are not in the Mac AppStore.

> homebrew cask install google-chrome

And you got the latest version of google Chrome installed. If you know how to deal with homebrew, you know how to deal with casks.

It´s also easy to make you own casks:

> homebrew cask create Volkersfreunde
>
> cd /usr/local/Library/Taps/phinze-cask/Casks
>
> git add Volkersfreunde.rb
>
> git commit -m”Just added a new cask”

Just start a pull request, and the world is a better place. I´ve added 3 recipes [already](https://github.com/phinze/homebrew-cask/pull/4122).

Cask can manage dmgs, zips, installers, quicklook plugins and some other types. The hardest part is to get the sha256 hash of the downloaded file.

> shasum -a 256

does the trick.

What are your favourite apps, available as cask recipes? This is my current list:

> adium hex-fiend airfoil hockey-app airserver hopper-disassembler android-file-transfer horndis android-studio imageoptim apns-pusher inkscape beaconscanner intellij-idea-ce beardedspice ios7-screensaver betterzipql iphone-configuration-utility bonjour-browser jsonlook caffeine mou carbon-copy-cloner mysqlworkbench charles pycharm-ce chromecast quicklook-csv chromium quicklook-json doxygen repetier-host fake find-any-file fluid simpholders flux sketchup freecad skype freemind slic3r genymotion sloth gfxcardstatus slowy gimp sourcetree github spark gitx-l spotify gity teleport google-chrome virtualbox google-hangouts vlc grandperspective webstorm handbrake wireshark
