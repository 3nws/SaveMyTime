#!/usr/bin/env python3

import requests
import time
import sys
import base64

from bs4 import BeautifulSoup

lockfile_path = ""
gamedir = ""
host, port = "https://127.0.0.1", ""
lobby_endpoint = "lol-champ-select/v1/session"
summoner_endpoint = "lol-summoner/v1/summoners"
ready_check_endpoint = "lol-matchmaking/v1/ready-check/accept"
password = ""
headers = {}
url = ""
stats_url = "https://lolprofile.net/summoner/"
region = ""
lobby_found = False

def main(args):
    global stats_url, port, host, url, headers, region, lobby_endpoint, summoner_endpoint, ready_check_endpoint, gamedir
    if len(args) > 0:
        with open("./path.txt", "w+") as f:
            f.write(args[0])
            lockfile_path = args[0] + "\\lockfile"
            gamedir = args[0]
    try:
        with open("./path.txt", "r") as f:
            gamedir = f.readline()
            lockfile_path = gamedir + "\\lockfile"
    except FileNotFoundError:
        print("Please run the script with the game directory as argument!")
        return
    try:
        with open(lockfile_path, "rb") as f:
            tmp = f.readline().decode().split(":")
            port = tmp[2]
            password = tmp[3]
            b64 = base64.b64encode(bytes(f"riot:{password}", "utf-8"))
            headers = {
                "Authorization": f"Basic {str(b64.decode())}",
                "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
            }
    except FileNotFoundError:
        print("Client has not been launched or the game directory is wrong!")
        return
    with open(gamedir + "\\Config\\LeagueClientSettings.yaml", "rb") as f:
        lines = f.readlines()
        for line in lines:
            if "region" in (found := line.decode()):
                tmp = eval("{"+found+"}")
                region = tmp[""]
                stats_url += region.lower() +"/"

def listen_to_champ_select():
    global stats_url, port, host, url, headers, region, lobby_endpoint, summoner_endpoint, ready_check_endpoint, gamedir, lobby_found
    url = f"{host}:{port}/{lobby_endpoint}"
    r = requests.get(url, headers=headers, verify="./riotgames.pem")
    res = r.json()
    if res.get("myTeam", None) is None:
        return
    player_ids = [player["summonerId"] for player in res.get("myTeam", None)]
    sumNames = []
    for player_id in player_ids:
        url = f"{host}:{port}/{summoner_endpoint}/{player_id}"
        res = requests.get(url, headers=headers, verify="./riotgames.pem")
        sumNames.append(res.json()["displayName"])
    winRates = []
    for sumName in sumNames:
        try:
            r = requests.get(stats_url + sumName)
            page = r.content
            soup = BeautifulSoup(page.decode("utf-8"), "html5lib")
            wrate = soup.find_all("div", "tooltip block s-wrb")[0]
            wrate = wrate.find("div")
            wrate = str(wrate)[5:-7]
            winRates.append(float(wrate))
        except Exception:
            print(f"Summoner profile could not be accessed for summoner: {sumName}!")
            continue
    print("Likely to win!" if (sum(winRates)/len(winRates)) > 50 else "Likely to lose!")
    print("Average win rate:", sum(winRates)/len(winRates))
    lobby_found = True

def listen_to_ready_check():
    requests.post(f"{host}:{port}/{ready_check_endpoint}", headers=headers, verify="./riotgames.pem")

if __name__ == "__main__":
    main(sys.argv[1:])
    while True:
        if not lobby_found:
            listen_to_champ_select()
        listen_to_ready_check()
        time.sleep(.5)