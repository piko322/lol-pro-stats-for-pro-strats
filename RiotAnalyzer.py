import requests
import pandas as pd
import time
from datetime import datetime

class RiotAnalyzer:
    """A class to get data from the Riot API
    """
    
    regionDict = {"NA": 'na1', "EUW": 'euw1', 'EUN': 'eun1', 'KR': 'kr', 'JP': 'jp1',
                  'OC': 'oc1', 'BR': 'br1', 'LA1': 'la1', 'LA2': 'la2', 'RU': 'ru', 'TR': 'tr1', "SG": 'sg2',
                  "LAN":'la1', "LAS": 'la2'}
    queueDict = {
        k: v
        for keys, v in [(['soloq', 'solo queue', 'solo'], "RANKED_SOLO_5x5"),
                        (['flexq', 'flex queue', 'flex'], "RANKED_FLEX_SR"),
                        (['tft', 'tt'], "RANKED_FLEX_TT")] for k in keys
    }
    
    tierDict = {'d': 'DIAMOND', 'e': 'EMERALD', 'p': 'PLATINUM', 'g': 'GOLD', 's': 'SILVER', 'b': 'BRONZE', 'i': 'IRON'}
    
    divisionDict = {"1": "I", "2": "II", "3": "III", "4": "IV"}


    def __init__(self, tokens:list, region="NA", version='13.17.1'):
        if region.upper() not in self.regionDict:
            raise Exception(f"Region {region} not found")
        region_code = self.regionDict[region.upper()]
        self.region_code = region_code
        
        self.tokens = tokens
        self.token = tokens[0]
        self.version = version
        
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8,ja;q=0.7",
            "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://developer.riotgames.com",
            "X-Riot-Token": self.token
        }
        self.url_template = "https://{region_code}.api.riotgames.com/lol/{endpoint}?{query}"
        self.champion_dict = None
        self.champion_dict = self.get_champion_dict(version)
        
    def swap_token(self):
        """Swaps the current token with the next token in the tokens list
        """
        current_idx = self.tokens.index(self.token)
        next_idx = (current_idx + 1) % len(self.tokens)
        self.token = self.tokens[next_idx]
        self.header["X-Riot-Token"] = self.token
        return self.token
        
    
    def get_champion_dict(self, version=None):
        """Gets a dictionary of champion names and their IDs

        Args:
            version (str): The version of the game to get the champion data for

        Returns:
            dict: A dictionary of champion names and their IDs
        """
        if not version:
            version = self.version
        elif self.champion_dict and version == self.version:
            return self.champion_dict
        url = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code} when querying champion data")
        data = response.json()
        champion_dict = {}
        for champion in data["data"]:
            champion_dict[data["data"][champion]["key"]] = data["data"][champion]["name"]
        self.champion_dict = champion_dict
        return champion_dict
    
    
    def get_champion_name(self, champion_code):
        return self.champion_dict[str(champion_code)]
    
    
    def get_leaderboard_raw(self, queue, rank:str, region=None, page=1):
        """Gets a certain page of the leaderboard for a specific queue, tier, and division. NOTE: It is not sorted.
        Returns the JSON response from the Riot API.

        Args:
            queue (str): The queue type to query for. Can be RANKED_SOLO_5x5, RANKED_FLEX_SR, RANKED_FLEX_TT
            tier (str): The tier to query for. Can be DIAMOND, EMERALD, PLATINUM, GOLD, SILVER, BRONZE, IRON
            division (str): The division to query for. Can be I, II, III, IV
            region (str, optional): The region to search the leaderboard for. Defaults to the region specified in the constructor.
        """
        queue = queue.lower()
        if queue not in self.queueDict:
            raise Exception(f"Queue {queue} not found")
        queue = self.queueDict[queue]
        
        if len(rank) != 2:
            raise Exception("Rank must be 2 characters long, and consists of {tier}{division}")
        
        tier = rank[0]
        tier = tier.lower()
        if tier not in self.tierDict:
            raise Exception(f"Tier {tier} not found")
        tier = self.tierDict[tier]
        
        division = rank[1]
        if division not in self.divisionDict:
            raise Exception(f"Division {division} not found")
        division = self.divisionDict[division]
        
        if region is None:
            region = self.region_code
        elif region.upper() not in self.regionDict:
            raise Exception(f"Region {region} not found")
                
        endpoint = f"league/v4/entries/{queue}/{tier}/{division}"
        
        url = self.url_template.format(region_code=self.region_code, endpoint=endpoint, query=f"page={page}")
        response = requests.get(url, headers=self.header)
        
        if response.status_code == 429:
            # If the request is rate limited, wait for the specified time and try again
            # Check if response.headers["Retry-After"] exists, if not, wait for 10 seconds
            if "Retry-After" not in response.headers:
                print("Rate limited, retrying in 30 seconds")
                time.sleep(30)
                return self.get_leaderboard_raw(queue, rank, region, page)
            else:
                retry_after = response.headers["Retry-After"]
                print(f"Rate limited, retrying in {retry_after} seconds")
                time.sleep(retry_after)
                return self.get_leaderboard_raw(queue, rank, region, page)
            
        elif response.status_code == 503:
            # If the server is unavailable, wait for 30 seconds and try again
            print("Server unavailable, retrying in 30 seconds")
            time.sleep(30)
            return self.get_leaderboard_raw(queue, rank, region, page)
        
        elif response.status_code != 200:
            raise Exception(
                f"Error {response.status_code} when querying leaderboard")
        data = response.json()

        return data


    def get_top(self, queue=None, rank=None, region="NA", n:int=20, start_page:int=1, page_limit:int=99999):
        """Takes in the JSON data from get_leaderboard_raw and converts it to a Pandas DataFrame containing the following columns in order:
        tier, division, rank, summonerId, summonerName, leaguePoints, wins, losses, veteran, inactive, freshBlood, queueType

        Args:
            data (json bytearray): The JSON data from get_leaderboard_raw
        """
        # Use a while loop to get all the pages of the leaderboard
        # For each page, take only the top 20 highest "leaguePoint" and discard the rest
        # On each subsequent iteration, also take the top 20, append that to the DataFrame, and again keep only the top 20
        # So each iteration will add 20 rows to the DataFrame, but then discard all but the top 20 rows among the 40 rows, by leaguePoints
        # This is done because the Riot API only returns 200 entries per page, and there are more than 200 entries in the leaderboard
        # So we have to get all the pages and then sort them ourselves
        if queue is None:
            raise Exception("Queue must be specified")
        if rank is None:
            raise Exception("Rank must be specified")
        
        page = start_page
        total_entries = 0
        result_df = pd.DataFrame()
        print("Queried pages: ", end="")
        while True and (page <= page_limit + start_page - 1):
            print(page, end=", ")
            # Add line break every 10 pages
            if page % 10 == 0:
                print()
            data = self.get_leaderboard_raw(queue, rank, region, page)
            # Exit the loop if there is no more data
            if data == []:
                break
            df = pd.DataFrame(data)
            
            # Add a new "Winrate" column to the DataFrame
            df["winrate"] = df["wins"] / (df["wins"] + df["losses"])
           
            # Add the total number of entries in the leaderboard to the total_entries variable
            total_entries += len(df)
            
            # Concatenate the new DataFrame to the result DataFrame
            result_df = pd.concat([result_df, df])
            
            # Sort the result DataFrame by leaguePoints, then winrate
            result_df = result_df.sort_values(by=["leaguePoints", "winrate"], ascending=False)
           
            # Keep only the top x amount rows (default 20)
            result_df = result_df.head(n)
            page += 1
        
        # Reset the index of the result DataFrame, drop the old index,
        # and rename the new index to "Rank"
        result_df = result_df.reset_index(drop=True)
        result_df.index.name = "Rank"
        result_df.index += 1
        print("Total entries:", total_entries)
    
        return result_df

    def get_puuid(self, name:str, region_code:str="NA"):
        if region_code in self.regionDict.keys():
            region_code = self.regionDict[region_code]
        url = self.url_template.format(region_code=region_code, endpoint="summoner/v4/summoners/by-name/"+name, query="page=1")

        response = requests.get(url, headers=self.header)
        if response.status_code != 200:
            raise Exception("Error with response code: {}".format(response.status_code))
        else:
            name_data = response.json()
            puuid = name_data["puuid"]
            return puuid
    
    def get_mastery(self, puuid:str, region_code:str="NA"):
        if region_code in self.regionDict.keys():
            region_code = self.regionDict[region_code]
        url = self.url_template.format(region_code=region_code, endpoint=f"champion-mastery/v4/champion-masteries/by-puuid/{puuid}", query="page=1")
        
        response = requests.get(url, headers=self.header)
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code} when querying mastery")
        else:
            return response.json()
    
    def get_mastery_by_summoner_name(self, name, region_code:str="NA"):

        if region_code in self.regionDict.keys():
            region_code = self.regionDict[region_code]
        elif region_code not in self.regionDict.values():
            raise Exception(f"Region {region_code} not found")
        
        puuid = self.get_puuid(name, region_code)
        mastery = self.get_mastery(puuid,region_code)
        df = pd.DataFrame(mastery)
        
        df["championName"] = df["championId"].apply(lambda x: self.get_champion_dict()[str(x)])
        df = df[["championName", "championLevel", "championPoints", "lastPlayTime"]]
        df["lastPlayDate"] = df["lastPlayTime"].apply(lambda x: datetime.fromtimestamp(x/1000))
        df["lastPlayTime"] = df["lastPlayTime"].apply(lambda x: datetime.fromtimestamp(x/1000).strftime("%b %d %H:%M"))
        df["percent"] = df["championPoints"]/df["championPoints"].sum()
        df["percent"] = df["percent"].apply(lambda x: "{:.2%}".format(x))
        df.index += 1
        df.index.name = "Rank"
        return df

    
