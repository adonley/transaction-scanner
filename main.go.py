import requests
import logging
import json
import os
import csv
import datetime
from ethereum import utils

logging.basicConfig(level=logging.INFO)
log_amount = 1000
csv_output_dir = "csv"


def make_rpc(method, params):
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 74
    }
    response = requests.post("http://127.0.0.1:8545", json=data)
    if response.status_code != 200:
        logging.warning(response.content)
    return json.loads(response.content).get('result')


def get_block_by_number(hex_number):
    logging.debug("Hex number: " + str(hex_number))
    return make_rpc("eth_getBlockByNumber", [hex_number, True])


def get_block_height():
    return int(make_rpc("eth_blockNumber", []), 16)


def is_contract(address):
    code = make_rpc("eth_getCode", [address, "latest"])
    if code == "0x":
        return False
    return True


def alter_balance(balances, address, value, operator="add"):
    if not address:
        logging.warning("Address was none")
        return

    if not balances.get(address):
        balances[address] = 0

    if operator == "add":
        balances[address] += value
    else:
        balances[address] -= value

    if balances[address] < 0:
        logging.warning("Balance for address {} was below 0. {}".format(address, balances[address]))


def get_balance(address):
    balance = make_rpc("eth_getBalance", [address, "latest"])
    return int(balance, 16) / utils.denoms.ether


def main():
    balances = dict()

    height = get_block_height()
    start = datetime.datetime.utcnow()
    for i in range(height):
        block = get_block_by_number(hex(i))

        balances[block.get('miner')] = True
        if not block.get('miner'):
            logging.warning("Miner address was None")

        # miner_reward = len(block.get('uncles')) * 5.0/32 + 5.0 + int(block.get('gasUsed'), 16)
        # alter_balance(balances, block.get('miner'), miner_reward)

        transactions = block.get("transactions")
        for transaction in transactions:
            # gas = int(transaction.get('gas'), 16)
            # gasPrice = int(transaction.get('gasPrice'), 16)
            # value = int(transaction.get('value'), 16) / utils.denoms.ether - (gas * gasPrice)
            # alter_balance(balances, transaction.get('to'), value)
            # alter_balance(balances, transaction.get('from'), value, "subtract")
            balances[transaction.get('to')] = True
            balances[transaction.get('from')] = True
            if not block.get('miner'):
                logging.warning("To address was None")
            if not block.get('miner'):
                logging.warning("From address was None")

        if i % log_amount == 0:
            end = datetime.datetime.utcnow()
            estimated_time = ((height - i) / log_amount) * (end - start).seconds / (60 * 60)
            start = end
            logging.info("Processed: {} blocks out of {} for addresses. Estimated time remaining: {} hours".format(i, height, estimated_time))

    if balances[None]:
        del balances[None]

    count = 0
    for address, _ in balances.items():
        balances[address] = get_balance(address)
        count += 1
        if count % log_amount == 0:
            logging.info("Processed {} out of {} address balances".format(count, len(balances)))

    if not os.path.exists(csv_output_dir):
        os.makedirs(csv_output_dir)

    with open(csv_output_dir + '/balances.csv', 'w') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        csv_writer.writerow(["address", "balance", "is contract"])
        for address, balance in balances.items():
            contract = is_contract(address)
            csv_writer.writerow([address, balance, contract])


if __name__ == "__main__":
    main()
