import ConfigParser


config = ConfigParser.ConfigParser()
config.read('Config.ini')
config.sections()

DownloadDirectory = config.get('GetYoutube', 'DownloadDirectory')
ListenAddr = config.get('GetYoutube','ListenAddr')
ListenPort = config.getint('GetYoutube', 'ListenPort')
EchoNestKey = config.get('GetYoutube', 'EchoNestKey')
NumConcurrentDownloads = config.getint('GetYoutube', 'NumConcurrentDownloads')

print NumConcurrentDownloads
      





