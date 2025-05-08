import streamlit as st
import os
from dotenv import load_dotenv
import requests
import pandas as pd
from forex_python.converter import CurrencyCodes
import yaml
from pathlib import Path

# Load colloquial denominations from a YAML file
def load_colloquial_denominations(file_path: str) -> dict[str, dict[str, int]]:
    with open(file_path, 'r') as file:
        # Add 'None' = 1 as the first value for every currency if it doesn't exist
        data = yaml.safe_load(file)
        for currency in data:
            if 'None' not in data[currency]:
                # Create a new dictionary with 'None' as the first key
                updated_dict = {'None': 1}
                # Add the existing key-value pairs to the updated dictionary
                updated_dict.update(data[currency])
                # Replace the original dictionary with the updated one
                data[currency] = updated_dict
        return data

def get_country_code():

    if (Path(__file__).parent / 'config' / 'config_default.env').exists():
        # Load the environment variables from the user defined config file
        config_env = Path(__file__).parent / 'config' / 'config.env'
    else:
        # if not found load the default config file
        config_env = Path(__file__).parent / 'config' / 'config_default.env'
    
    load_dotenv(config_env)
    print(f'Loading config file from {config_env}')
    api_key = os.getenv("XCNG_API_TOKEN")
    api_url = f'{os.getenv("XCNG_API_URL")}/{api_key}/codes'
    
    res = requests.get(api_url).json()
    country = res['supported_codes']

    code = []
    for i in country:
        code.append(i[0])

    return code

def converter(base, target, amount, colloquial_denominations):
    if (Path(__file__).parent / 'config' / 'config_default.env').exists():
        # Load the environment variables from the user defined config file
        config_env = Path(__file__).parent / 'config' / 'config.env'
    else:
        # if not found load the default config file
        config_env = Path(__file__).parent / 'config' / 'config_default.env'
    
    load_dotenv(config_env)
    api_key = os.getenv("XCNG_API_TOKEN")
    api_url = f'{os.getenv("XCNG_API_URL")}/{api_key}/pair/{base}/{target}/{amount}'

    res = requests.get(api_url).json()
    base_code = res['base_code']
    target_code = res['target_code']
    rate = res['conversion_rate']
    result = res['conversion_result']

    base_symbol = CurrencyCodes().get_symbol(base_code)
    target_symbol = CurrencyCodes().get_symbol(target_code)

    # Display the conversion result
  

    # put the whole result in a table

    conversion_data = {
        'From Currency': [f'{base_symbol} {amount:0,.0f} {base_code}'],
        'Exchange Rate': [f'{target_symbol} {rate:0,.1f} (1 {base_code} -> {target_code})'],
        'Converted Amount': [f'{target_symbol} {result:0,.1f} {target_code}'],
    }
    conversion_df = pd.DataFrame(conversion_data)
    st.table(conversion_df)
    
    
    st.text('In other denominations:')

    # Display the conversion results in colloquial denominations
    if target_code in colloquial_denominations:
        denominations = colloquial_denominations[target_code]
        
        colloquial_data = {
            'Converted Amount': []
        }
        
        for denomination, value in denominations.items():
            converted_amount = result / value
            if denomination == 'None' or converted_amount < 1:
                continue
            colloquial_data['Converted Amount'].append(f'{target_symbol} {converted_amount:.2f} {denomination}')
        
        colloquial_df = pd.DataFrame(colloquial_data)
        st.table(colloquial_df)
    else:
        st.text(f'Converted Amount: {result}')

def main():
    st.title('Colloquial Currency Converter')
    st.sidebar.header('Change denomination type')

    # Yaml file containing colloquial denominations. Located in the config folder   
    if (Path(__file__).parent / 'config' / 'colloquial_denominations.yml').exists():
        # Load the data from the user defined colloquial denominations
        yaml_file_path = Path(__file__).parent / 'config' / 'colloquial_denominations.yml'
    else:
        # if not found load the default colloquial denominations file
        yaml_file_path = Path(__file__).parent / 'config' / 'colloquial_denominations_default.yml'

    # Check if the file exists
    if not os.path.exists(yaml_file_path):
        st.error(f"Config YAML file not found at {yaml_file_path}")
        return

    # Load the denominations into a dictionary
    colloquial_denominations = load_colloquial_denominations(yaml_file_path)

    if (Path(__file__).parent / 'config' / 'config.env').exists():
        # Load the environment variables from the user defined config file
        config_env = Path(__file__).parent / 'config' / 'config.env'
    else:
        # if not found load the default config file
        config_env = Path(__file__).parent / 'config' / 'config_default.env'

    if not os.path.exists(config_env):
        st.error(f"Config file not found at {config_env}")
        return

    # Initialize session state variables if they don't exist
    if 'from_currency' not in st.session_state:
        st.session_state.from_currency = 'USD'
    if 'to_currency' not in st.session_state:
        st.session_state.to_currency = 'INR'
        
    code = get_country_code()
    
    op = st.sidebar.selectbox('Select an option', ['Colloquial', 'Fixed'], index=0, 
                              help='Colloquial: 1 Million, 1 Lakh, etc.\nFixed: 1, 10, 100, etc.')
    


    with st.sidebar.popover('Config Settings Info', icon="⚙️", 
                        help='See the loaded config files '):
        st.write('Colloquial denominations file:')
        with open(yaml_file_path, 'r') as file:
            deno_content = file.read()
        st.code(deno_content, language='yaml')
        st.write("Path:", yaml_file_path)
        st.write('Config file:')
        with open(config_env, 'r') as file:
            config_content = file.read()
        st.code(config_content, language='cfg')
        st.write("Path:", config_env)

    # Display the select boxes for currency selection

    col1, col2, col3 = st.columns(3, vertical_alignment="bottom", border=False)
    with col1:
        fromCurrency = st.selectbox('Enter the base currency', code, 
                                    index=code.index(st.session_state.from_currency))

    with col2:
        toCurrency = st.selectbox('Enter the target currency', code, 
                                    index=code.index(st.session_state.to_currency))

    # Update session state when select boxes change
    st.session_state.from_currency = fromCurrency
    st.session_state.to_currency = toCurrency
    
    with col3:
        # Handle the switch button
        if st.button('Switch', icon="🔄", use_container_width=True):
            # Swap the values in session state
            st.session_state.from_currency, st.session_state.to_currency = st.session_state.to_currency, st.session_state.from_currency
            # Force a rerun to update the UI
            st.rerun()

    # Display the amount input

    amount=st.number_input('Enter the amount', value=1, step=1, min_value=0, max_value=1_000_000_000, icon="💵")

    col1, col2 = st.columns(2, vertical_alignment="bottom", border=False)

    # show col1 for colloquial only if colloquial_denominations exist for the selected from currency
    if st.session_state.from_currency in colloquial_denominations:
        col1, col2 = st.columns(2, vertical_alignment="bottom", border=False)
        with col1:
            if op == 'Fixed':
                st.session_state.denomination = st.radio('Select the multiplier', ('1', '10', '100', '1000', '10000'), index=0, horizontal=True)    
            elif op == 'Colloquial':
                if st.session_state.from_currency in colloquial_denominations:
                    # Get the colloquial denominations for the selected currency
                    denominations = colloquial_denominations[st.session_state.from_currency]
                    # Create a select box with the colloquial denominations
                    st.session_state.denomination = st.selectbox('Select the multiplier', list(denominations.keys()), index=0)
                    # retrieve the value of the selected denomination and store its value in session state
                    # Convert the selected denomination to its value
                    st.session_state.denomination = denominations[st.session_state.denomination]

        with col2:
            # Use the current value from session state for amount
            denomination = st.session_state.denomination
            # Convert the string to an integer
            denomination = int(denomination)
            denomination = st.number_input('Enter multiplier value', value=denomination, step=1, min_value=0, max_value=1_000_000_000)
    else:
        
        # Use the current value from session state for amount
        denomination = st.session_state.denomination
        # Convert the string to an integer
        denomination = int(denomination)
        denomination = st.number_input('Enter multiplier value', value=denomination, step=1, min_value=0, max_value=1_000_000_000)


    st.text("" * 5)
    # Use the current values from session state for conversion
    if st.session_state.from_currency != st.session_state.to_currency:
        if st.button('Convert', type="primary", use_container_width=True):
            # Display the conversion result
            st.divider()
            st.subheader('Conversion Result')
            converter(st.session_state.from_currency, st.session_state.to_currency, amount * denomination, colloquial_denominations)


if __name__ == '__main__':
    main()