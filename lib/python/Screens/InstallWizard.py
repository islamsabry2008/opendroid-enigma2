from os import system
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigBoolean, getConfigListEntry, ConfigSelection, ConfigYesNo, ConfigIP
from Components.Network import iNetwork
from Components.Opkg import OpkgComponent
from Components.Sources.StaticText import StaticText
from enigma import eDVBDB

config.misc.installwizard = ConfigSubsection()
config.misc.installwizard.hasnetwork = ConfigBoolean(default=False)
config.misc.installwizard.ipkgloaded = ConfigBoolean(default=False)
config.misc.installwizard.channellistdownloaded = ConfigBoolean(default=False)


class InstallWizard(Screen, ConfigListScreen):

	STATE_UPDATE = 0
	STATE_CHOISE_CHANNELLIST = 1
	INSTALL_PLUGINS = 2
	INSTALL_SKINS = 3
	INSTALL_NETWORkPASSWORD = 4

	def __init__(self, session, args=None):
		Screen.__init__(self, session)

		self.index = args
		self.list = []
		ConfigListScreen.__init__(self, self.list)

		if self.index == self.STATE_UPDATE:
			config.misc.installwizard.hasnetwork.value = False
			config.misc.installwizard.ipkgloaded.value = False
			modes = {0: " "}
			self.enabled = ConfigSelection(choices=modes, default=0)
			self.adapters = [(iNetwork.getFriendlyAdapterName(x), x) for x in iNetwork.getAdapterList()]
			is_found = False
			for x in self.adapters:
				if x[1] in ("eth0", "eth1"):
					if iNetwork.getAdapterAttribute(x[1], "up"):
						self.ipConfigEntry = ConfigIP(default=iNetwork.getAdapterAttribute(x[1], "ip"))
						iNetwork.checkNetworkState(self.checkNetworkCB)
						is_found = True
					else:
						iNetwork.restartNetwork(self.checkNetworkLinkCB)
					break
			if is_found is False:
				self.createMenu()
		elif self.index == self.STATE_CHOISE_CHANNELLIST:
			self.enabled = ConfigYesNo(default=True)
			modes = {"opendroid": "opendroid default(13e-19e)", "19e": "Astra 1", "23e": "Astra 3", "19e-23e": "Astra 1 Astra 3", "19e-23e-28e": "Astra 1 Astra 2 Astra 3", "13e-19e-23e-28e": "Astra 1 Astra 2 Astra 3 Hotbird"}
			self.channellist_type = ConfigSelection(choices=modes, default="opendroid")
			self.createMenu()
		elif self.index == self.INSTALL_PLUGINS:
			self.enabled = ConfigYesNo(default = False)
			self.createMenu()
		elif self.index == self.INSTALL_SKINS:
			self.enabled = ConfigYesNo(default = False)
			self.createMenu()
		elif self.index == self.INSTALL_NETWORkPASSWORD:
			self.enabled = ConfigYesNo(default = True)
			self.createMenu()

	def checkNetworkCB(self, data):
		if data < 3:
			config.misc.installwizard.hasnetwork.value = True
		self.createMenu()

	def checkNetworkLinkCB(self, retval):
		if retval:
			iNetwork.checkNetworkState(self.checkNetworkCB)
		else:
			self.createMenu()

	def createMenu(self):
		try:
			test = self.index
		except Exception:
			return
		self.list = []
		if self.index == self.STATE_UPDATE:
			if config.misc.installwizard.hasnetwork.value:
				self.list.append(getConfigListEntry(_("Your internet connection is working (ip: %s)") % (self.ipConfigEntry.getText()), self.enabled))
			else:
				self.list.append(getConfigListEntry(_("Your receiver does not have an internet connection"), self.enabled))
		elif self.index == self.STATE_CHOISE_CHANNELLIST:
			self.list.append(getConfigListEntry(_("Install channel list"), self.enabled))
			if self.enabled.value:
				self.list.append(getConfigListEntry(_("Channel list type"), self.channellist_type))
		elif self.index == self.INSTALL_PLUGINS:
			self.list.append(getConfigListEntry(_("Do you want to install plugins"), self.enabled))
		elif self.index == self.INSTALL_SKINS:
			self.list.append(getConfigListEntry(_("Do you want to change the default skin"), self.enabled))
		elif self.index == self.INSTALL_NETWORkPASSWORD:
			self.list.append(getConfigListEntry(_("To access the network services enter the password"), self.enabled))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyLeft(self):
		if self.index == 0:
			return
		ConfigListScreen.keyLeft(self)
		self.createMenu()

	def keyRight(self):
		if self.index == 0:
			return
		ConfigListScreen.keyRight(self)
		self.createMenu()

	def run(self):
		if self.index == self.STATE_UPDATE:
			if config.misc.installwizard.hasnetwork.value:
				self.session.open(InstallWizardOpkgUpdater, self.index, _('Please wait (updating packages)'), OpkgComponent.CMD_UPDATE)
		elif self.index == self.STATE_CHOISE_CHANNELLIST and self.enabled.value:
			self.session.open(InstallWizardOpkgUpdater, self.index, _('Please wait (downloading channel list)'), OpkgComponent.CMD_REMOVE, {'package': 'enigma2-plugin-settings-' + self.channellist_type.value})
		elif self.index == self.INSTALL_PLUGINS and self.enabled.value:
			from Screens.PluginBrowser import PluginDownloadBrowser
			self.session.open(PluginDownloadBrowser, 0)
		elif self.index == self.INSTALL_SKINS and self.enabled.value:
			from Screens.SkinSelector import SkinSelector
			self.session.open(SkinSelector)
		elif self.index == self.INSTALL_NETWORkPASSWORD and self.enabled.value:
			from Screens.NetworkSetup import NetworkPassword
			self.session.open(NetworkPassword)
		return


class InstallWizardOpkgUpdater(Screen):
	def __init__(self, session, index, info, cmd, pkg=None):
		Screen.__init__(self, session)

		self["statusbar"] = StaticText(info)

		self.pkg = pkg
		self.index = index
		self.state = 0

		self.opkg = OpkgComponent()
		self.opkg.addCallback(self.opkgCallback)

		if self.index == InstallWizard.STATE_CHOISE_CHANNELLIST:
			self.opkg.startCmd(cmd, {'package': 'enigma2-plugin-settings-*'})
		else:
			self.opkg.startCmd(cmd, pkg)

	def opkgCallback(self, event, param):
		if event == OpkgComponent.EVENT_DONE:
			if self.index == InstallWizard.STATE_UPDATE:
				config.misc.installwizard.ipkgloaded.value = True
			elif self.index == InstallWizard.STATE_CHOISE_CHANNELLIST:
				if self.state == 0:
					self.opkg.startCmd(OpkgComponent.CMD_INSTALL, self.pkg)
					self.state = 1
					return
				else:
					config.misc.installwizard.channellistdownloaded.value = True
					eDVBDB.getInstance().reloadBouquets()
					eDVBDB.getInstance().reloadServicelist()
			self.close()
