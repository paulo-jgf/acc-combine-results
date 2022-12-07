# -*- coding: utf-8 -*-
"""
Created on Wed Dec  7 08:13:52 2022

@author: paulo
"""

import pandas as pd
from datetime import datetime
import re
import bs4
import requests

#Example urls
#urls = ['https://dkgoraceacc.emperorservers.com/results/221206_230542_FP',
#        'https://dkgoraceacc.emperorservers.com/results/221206_225612_FP',
#        'https://dkgoraceacc.emperorservers.com/results/221205_194502_FP']

def urlAuto():
    base_url = 'https://dkgoraceacc.emperorservers.com/results?page={}'
    urls_auto = []
    
    for pg in range(10):
        res = requests.get(base_url.format(pg))    
        soup = bs4.BeautifulSoup(res.text, 'html.parser')    
        results = soup.find_all('tr', {'class': 'row-link'})
        
        print('Get urls page ', pg)
        
        if not results:
            break
        
        for r in results:
            urls_auto.append('https://dkgoraceacc.emperorservers.com{}'.format(
                    r['data-href']))
            
    return urls_auto

def timeMath(x):
    parsed = datetime.strptime(x, '%M:%S.%f')
    woYear = parsed - datetime.strptime('0:0.0', '%M:%S.%f')
    inSecWithMiliSec = woYear.total_seconds()
    return inSecWithMiliSec

def fixStrings(x):    
    return ' '.join(x.split()[:-1]).strip()

def fixLapNumber(x):
    return int(re.sub('\D','', x))

def fixLapTime(s):
    ms = str(s).split('.')[-1]
    while len(ms) < 3:
        ms += '0'    
    mi = int(s/60)
    sremaind = int(s) % (mi*60)    
    return '{}:{}.{}'.format(mi, sremaind, ms)    

def main():
    urls = urlAuto()
    
    cdf = []
    
    for url in urls:
        print('Get session: ', url)
        dfs = pd.read_html(url)
        
        if dfs:
            df = dfs[0]
            
            if 'Best Practice Lap' in df.columns:
                cdf.append(df)
                
    df = pd.concat(cdf)
    # Discard invalid bests
    df = df[df['Best Practice Lap'] != '00:00.000']
    
    def create_fixed_df(X):
        
        ndf.append({
                    'Driver': fixStrings(X['Name']),
                    'Car': fixStrings(X['Car']),
                    'Best Practice Lap': X['Best Practice Lap'],
                    'Laps': fixLapNumber(X['Laps']),
                    'bLapS': timeMath(X['Best Practice Lap'])
                    })
        
    
    ndf = []
    df.apply(create_fixed_df, axis=1)
    ndf = pd.DataFrame(ndf)
    
    fdf = ndf.groupby(['Driver', 'Car'], as_index=False).agg(
            {'bLapS': "min", 'Laps': "sum"}
        )
    
    fdf.sort_values('bLapS', inplace=True)
    fdf.reset_index(drop=True, inplace=True)
    fdf.rename_axis("Position", axis="columns", inplace=True)
    
    fdf['Best lap time'] = fdf['bLapS'].apply(lambda x: fixLapTime(x))
    
    cols = ['Driver', 'Car', 'Best lap time', 'Laps']
    fdf.index += 1
    html = '<html>\n{}\n</html>'.format(fdf[cols].to_html())
    
    with open('combined_results.html', 'w') as f:
        f.write(html)


if __name__ == "__main__":
    main()



