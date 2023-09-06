import requests
import pandas as pd

class RiotAnalyzer:
    """A class to get data from the Riot API
    """
    regionDict = {"NA1": 'na1', "EUW1": 'euw1', 'EUN1': 'eun1', 'KR': 'kr', 'JP1': 'jp1',
                  'OC1': 'oc1', 'BR1': 'br1', 'LA1': 'la1', 'LA2': 'la2', 'RU': 'ru', 'TR1': 'tr1'}
    queueDict = {
        k: v
        for keys, v in [(['soloq', 'solo queue', 'solo'], "RANKED_SOLO_5x5"),
                        (['flexq', 'flex queue', 'flex'], "RANKED_FLEX_SR"),
                        (['tft', 'tt'], "RANKED_FLEX_TT")] for k in keys
    }
    tierDict = {'d': 'DIAMOND', 'e': 'EMERALD', 'p': 'PLATINUM', 'g': 'GOLD', 's': 'SILVER', 'b': 'BRONZE', 'i': 'IRON'}
    divisionDict = {"1": "I", "2": "II", "3": "III", "4": "IV"}

    def __init__(self, token, region="NA1"):
        if region.upper() not in self.regionDict:
            raise Exception(f"Region {region} not found")
        region_code = self.regionDict[region.upper()]
        self.token = token
        self.region_code = region_code
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8,ja;q=0.7",
            "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://developer.riotgames.com",
            "X-Riot-Token": "RGAPI-9c72c116-9d41-4245-8af9-e431b87bf6cc"
        }
        self.url_template = "https://{region_code}.api.riotgames.com/lol/{endpoint}?{query}"
    
    def get_leaderboard_raw(self, queue, rank:str, region=None):
        """Get the leaderboard for a specific queue, tier, and division.
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
        
        url = self.url_template.format(region_code=self.region_code, endpoint=endpoint, query="page=1")
        response = requests.get(url, headers=self.header)
        
        if response.status_code != 200:
            raise Exception(
                f"Error {response.status_code} when querying leaderboard")
        data = response.json()

        return data

    def get_top_20(self, data=None, queue=None, rank=None, region=None):
        """Takes in the JSON data from get_leaderboard_raw and converts it to a Pandas DataFrame containing the following columns in order:
        tier, division, rank, summonerId, summonerName, leaguePoints, wins, losses, veteran, inactive, freshBlood, queueType

        Args:
            data (json bytearray): The JSON data from get_leaderboard_raw
        """
        # If data is not provided, get it from the Riot API
        if data is None:
            data = self.get_leaderboard_raw(queue, rank, region)
        
        df = pd.DataFrame(data)
        df = df[["tier", "rank", "summonerName", "leaguePoints", "wins", "losses", "veteran", "inactive", "freshBlood", "hotStreak",'queueType', "summonerId"]]
        
        # Add a "Leaderboard Rank" column to the DataFrame and sort by it
        df["Leaderboard Rank"] = df["leaguePoints"].rank(method='dense', ascending=False)
        df = df.set_index("Leaderboard Rank")
        df = df.sort_index()

        return df.head(20)
