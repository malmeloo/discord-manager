# Discord Manager

> **Warning**
> This project is currently in **ALPHA**. Things might not work as expected.
> If you encounter any issues, please file a bug report. Thanks!

Discord Manager (a.k.a. _disman_) is a flexible command-line program that allows you to manage your discord instances.
It allows you to keep your instances completely sandboxed from each other and conveniently switch between them whenever you want.

For example, you could have the following setups installed at the same time:
* Discord
* Discord Canary
* Discord Canary - [Replugged](https://replugged.dev/)
* Discord Canary - [BetterDiscord](https://betterdiscord.app)

...and none of them would interfere with each other. Magical!

## Current Features
* Create, delete and list instance "slots"
* Initialize and upgrade slots to latest or custom version
* Launch instances using a single command

## Limitations
* Only tested on Linux. Please create an issue if you want to help test other platforms.
* You cannot run multiple instances at the same time if they are the same edition (stable, ptb, canary)
  * This is a limitation with Discord and while I have some ideas, no concrete plans have been created to fix this

## Planned features
* Config migration
  * Migrates config from existing, official discord to disman
* Comprehensive plugin system
  * My ideal target for this project is a slim base with an extensive plugin system to build new features with
  * This would ideally also include plugin (un)loading and (automatic?) updates through disman
  * For complete integration, plugins would have access to registering custom commands, instance management hooks and more
* Instance backup/restore to move discord across systems (portable discord setup anyone???)
  * This could potentially even be cross-platform if we strip the modules when backing up
