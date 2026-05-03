from parser import ConfigParser
from display import display

if __name__ == "__main__":
    data = ConfigParser('file.txt', {})
    display = display(data.parse()['hubs'], data.parse()['connections'])
    display.display_hubs()
