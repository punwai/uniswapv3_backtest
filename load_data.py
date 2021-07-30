
import requests
import json
import pandas as pd
import math
import numpy as np


# function to use requests.post to make an API call to the subgraph url
def run_query(q):

    # endpoint where you are making the request
    request = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
                            '',json={'query': q})
    if request.status_code == 200:
        return request
    else:
        raise Exception('Query failed. return code is {}.      {}'.format(request.status_code, query))
        
        


def get_token_id(symbol):
    
    # default should be first:10, in case there are more than 1 coins with the same symbol
    query_ = """ 
    {{
      tokens(first:1, where:{{symbol: "{}"}}) {{
        id
        symbol
        name
      }}
    }}""".format(symbol)
    
    # run query
    query_result_ = run_query(query_)
    json_data_ = json.loads(query_result_.text)
    
    print(' ')
    print('get_token_id: {}'.format(symbol))
    print(json_data_)
    
    # make sure only return 1 object
    if len(json_data_['data']['tokens']) == 1:
        token_id_ = json_data_['data']['tokens'][0]['id']
        return token_id_
        
    else:
        print(json_data_['data'])
        raise Exception('Returned number of token_ids != 1')

        



def get_pool_id(token0_id, token1_id, feeTier):
    query_ = """
    {{
      pools(first: 10, 
        where:{{token0: "{}",
        token1: "{}",
        feeTier:"{}" }}) 
      {{
        id
        token0{{symbol}}
        token1{{symbol}}
        feeTier
      }}
    }}""".format(token0_id, token1_id, feeTier)
    
    
    # run query
    query_result_ = run_query(query_)
    json_data_ = json.loads(query_result_.text)
    
    print('\n get_pool_id for feeTier: {}'.format(feeTier))
    print(json_data_)
    
    # make sure there is only 1 pool that matches exactly
    if len(json_data_['data']['pools']) == 1:
        pool_id_ = json_data_['data']['pools'][0]['id']
        return pool_id_
    else:
        print(json_data_['data'])
        raise Exception('Returned number of token_ids != 1')

        
    return json_data_





def get_poolHourDatas(pool_id, num_datapoints=3000):
    # input: pool_id
    # num_datapoints (must be multiple of max_request_)
    
    max_request_ = 1000
    quotient_ = math.floor(num_datapoints/max_request_)
            
    query_base_ = '''
    {{
      poolHourDatas(first:{},
      skip: {},
        where:{{ pool: "{}" }},
      orderBy:periodStartUnix,
      orderDirection: desc) 
      {{
        periodStartUnix
        pool{{
            token0{{
                symbol
            }}
            token1{{
                symbol
            }}
        }}
        liquidity
        sqrtPrice
        token0Price
        token1Price
        tick
        feeGrowthGlobal0X128
        feeGrowthGlobal1X128
        tvlUSD
        volumeToken0
        volumeToken1
        volumeUSD
        feesUSD
        txCount
        open
        high
        low
        close
      }}
    }}'''
    
    poolDayDatas_array_ = []
    
    # query loop
    for i in range(quotient_):
        q_first_ = max_request_
        q_next_ = i*max_request_
        query_ = query_base_.format(q_first_, q_next_, pool_id)
        query_result_ = run_query(query_)
        json_data_ = json.loads(query_result_.text)
        try:
            poolDayDatas_array_ += json_data_['data']['poolHourDatas']
        except Exception:
            pass
    
    print(' ')
    print('\n Queried poolHourDatas, total of {} datapoints'.format(str(len(poolDayDatas_array_))))

    
    # array to dataframe
    df_ = pd.json_normalize(poolDayDatas_array_)
    
    return df_





def get_swaps(pool_id, time_start='1627369200', time_end='1623772800', num_datapoints=6000):
    # input: pool_id
    # num_datapoints (must be multiple of max_request_)
    
    max_request_ = 1000
    quotient_ = math.floor(num_datapoints/max_request_)
#     remainder_ = num_datapoints%max_request_
           
    query_base_ = '''
    {{
      swaps(first:{}, skip: {},
            where:{{ pool: "{}",
            timestamp_lt: "{}",
            timestamp_gt: "{}"}},
          orderBy:timestamp,
          orderDirection: desc){{
        transaction {{
          blockNumber
          timestamp
          gasUsed
          gasPrice
        }}
        id
        timestamp
        tick
        amount0
        amount1
        amountUSD
        sqrtPriceX96
      }}
    }}'''
    
    swap_arrays_ = []
    
    # query loop
    for i in range(quotient_):
        q_first_ = max_request_
        q_next_ = i*max_request_
        query_ = query_base_.format(q_first_, q_next_, pool_id, time_start, time_end)
        query_result_ = run_query(query_)
        json_data_ = json.loads(query_result_.text)
        
        try:
            swap_arrays_ += json_data_['data']['swaps']
            
        except Exception:
            pass
        
    print('Queried Swaps, total of {} datapoints'.format(str(len(swap_arrays_))))
    print(' ')
    df_ = pd.json_normalize(swap_arrays_)
    
    # next time start, if at the edge, then we keep looping and skipping
    if len(swap_arrays_) != 0:
        # last element of timestamp, add 1 so next iterations still includes it
        next_time_start_ = str( int(df_['timestamp'][df_.index[-1]]) + 1 )
    else:
        next_time_start_ = time_start
            
            
    return df_, next_time_start_


# get_swap can only request 6000 datapoints at the time. this is to loop get_swap to get more data
def get_swaps_loop(pool_id, time_start='1627369200', time_end='1623772800'): # ,  num_datapoints= 150000
    
    print('time_start: {}, time_end: {}'.format(time_start, time_end))
    
    max_num_query = 6000
#     num_iterations = math.floor(num_datapoints/max_num_query) + 3 # add 3 just in case
    
    next_time_start_ = time_start
    count = 0 # counting number of times that data returns is less than maximum, meaning reaching the end
#     for i in range(num_iterations):
    first_time = True
    while(count<10):
        print('next_time_start_: {}'.format(next_time_start_))
        df_, next_time_start_ = get_swaps(pool_id, next_time_start_, time_end, num_datapoints=max_num_query)
        
        if first_time == True:
            df_all_ = df_
            first_time = False
        else:
            df_all_ = df_all_.append(df_)
            
        if df_.shape[0] < 6000:
            count += 1
    
    # drop duplicates, reset index
    df_all_ = df_all_.drop_duplicates(subset=['id'])
    df_all_ = df_all_.reset_index(drop=True)
    print('Total swaps data = {}'.format(df_all_.shape[0]))
    
    return df_all_







def merge_poolHourData_swaps_all(df_poolHourDatas, df_swaps_all):
    
    # Match timestamp with hour period, and assign to df_swaps_all['periodStartUnix']
    def compute_periodStartUnix(row_):
        return row_['timestamp'] - (row_['timestamp'] % 3600)
    def compute_periodEndUnix(row_):
        return row_['periodStartUnix'] + 3600

    df_swaps_all['timestamp'] = df_swaps_all['timestamp'].astype(int)    
    df_swaps_all['periodStartUnix'] = df_swaps_all.apply(lambda row: compute_periodStartUnix(row), axis=1)                       
    df_swaps_all['periodEndUnix'] = df_swaps_all.apply(lambda row: compute_periodEndUnix(row), axis=1)                       

    df_swaps_all['periodStartUnix'] = df_swaps_all['periodStartUnix'].astype(int)        
    df_swaps_all['periodEndUnix'] = df_swaps_all['periodEndUnix'].astype(int)
    
    # Create swaps_txCount to compare with txCount in poolHourDatas to check integrity
    df_swaps_all['swaps_txCount'] = 1

    # Groupby->Sum based on periodStartUnix, specify columns to sum at GROUPBY_COLS
    GROUPBY_COLS = ['periodStartUnix','amount0', 'amount1', 'amountUSD', 'swaps_txCount']
    df_swaps_to_merge = df_swaps_all[GROUPBY_COLS]
    df_swaps_to_merge = df_swaps_to_merge.astype({'periodStartUnix': 'int',
                                                 'amount0':'float','amount1':'float', 
                                                  'amountUSD':'float', 'swaps_txCount':'int'})
    df_swaps_to_merge = df_swaps_to_merge.groupby(by=['periodStartUnix']).sum()

    # Merge df_swaps_all (groupby) with df_poolHourDatas
    df_poolHourDatas['periodStartUnix'] = df_poolHourDatas['periodStartUnix'].astype(int)
    df_merged = df_poolHourDatas.merge(df_swaps_to_merge, how='left', on='periodStartUnix')
    df_merged['txCount'] = df_merged['txCount'].astype(int)
    
    return df_merged




def get_data(token0, token1, feeTier):
    
    # Indicate Tokens and FeeTier
    token0_id = get_token_id(TOKEN0)
    token1_id = get_token_id(TOKEN1)
    pool_id = get_pool_id(token0_id, token1_id, feeTier)

    # Get poolHourDatas
    df_poolHourDatas = get_poolHourDatas(pool_id, num_datapoints=10000)

    # Get Swap Datas within the poolHourDatas timeframe
    time_start = df_poolHourDatas['periodStartUnix'][0]
    time_end = df_poolHourDatas['periodStartUnix'][df_poolHourDatas.index[-1]]
    
    # Get Swaps data
    df_swaps_all = get_swaps_loop(pool_id, time_start, time_end) # ,  num_datapoints= 150000
    
    # Saving settings
    SETTINGS = '{}-{}-{}-timestamp-{}-{}.csv'.format(TOKEN0, TOKEN1, feeTier, time_start, time_end)
    df_swaps_all.to_csv('../data/df_swaps_all_'+SETTINGS)
    df_poolHourDatas.to_csv('../data/df_poolHourDatas_'+SETTINGS)
    
    # Merge data
    df_merged = merge_poolHourData_swaps_all(df_poolHourDatas, df_swaps_all)
    
    df_merged.to_csv('../data/df_merged_tmp_'+SETTINGS)
    
    return df_merged
















# #### Data we need:
# user input:
# - investment amount, trading pair -> amt0, amt1
# - start time and end time
# - time period that you assume fixed swap price, swap volumes or liquidity positions
# - upper and lower price
# - pool_fee_rate

# data from api:
# - cprice of each time period (tick, 1.0001 ** i)
# - L_pool at each time period at specific pool_fee_rate (liquidity?, or simply total X tokens + Y tokens in USD)
# - Swap volume at each time period at specific pool_fee_rate (volumeUSD?)
# - Gas cost to mint at each time period

# --------------------------------------------------------------------------------------------------------------
# #### Fees
# The liquidity amount is calculated from the following numbers that describe a position: 
# - amount of token 0 (amt0), amount of token 1 (amt1), 
# - price (as x token 1's per token 0) at the upper limit of the position (upper), 
# - price at the lower limit of the position (lower) 
# - and the current swap price (cprice). 

# Then liquidity (L_you?) for a position is calculated as follows:

# Case 1: cprice <= lower
# - liquidity = amt0 * (sqrt(upper) * sqrt(lower)) / (sqrt(upper) - sqrt(lower))

# Case 2: lower < cprice <= upper
# - liquidity is the min of the following two calculations:
# - amt0 * (sqrt(upper) * sqrt(cprice)) / (sqrt(upper) - sqrt(cprice))
# - amt1 / (sqrt(cprice) - sqrt(lower))

# Case 3: upper < cprice
# - liquidity = amt1 / (sqrt(upper) - sqrt(lower))

# Resources
# - liquidity can use this code: https://github.com/JNP777/UNI_V3-Liquitidy-amounts-calcs/blob/main/UNI_v3_funcs.py

# Fee is calculated by:
# - Fee income = (L_you/L_pool) * swap volume under fixed time period * pool_fee_rate/100
# - L_you also should be for that specific ticks only, not the whole amount you provided for. Its not linear, its calculated from the 3 cases above
# - Does Case1 and Case3's fee be 0 regardless?


# reference: https://uniswapv3.flipsidecrypto.com/
# - check my numbers with the reference from the website

# ----------------------------------------------------------------------------------------
# #### Impermanent Loss (is this v2 or v3)
# - IL (in %) = (2 sqrt(p) / (p+1) ) - 1
# - where p = r_t1/r_t2
# - and r_t is a price in b at time 1
# - Net $ loss = total asset value in dollars at stake time * IL (in%)

# reference: https://chainbulletin.com/impermanent-loss-explained-with-examples-math/#:~:text=Impermanent%20loss%20is%20the%20difference,is%20equal%20to%20200%20DAI

# --------------------------------------------------------------------------------------------------------------
# #### Other cost

# Gas_costs_mint = 500000 gwei * gas_price at that time (??? double check actual cost)

# ### PNL/APR
# -PNL = Acumulated Fees_accrued (dolar value at generation) - IL - Gas_costs_mint

# -APR = PNL/Initial_capital*(age of the position / year time)

# --------------------------------------------------------------------------------------------------------------
