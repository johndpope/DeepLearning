import logging
from pprint import pprint
from datetime import datetime
import csv

import deepstock
from agent import Agent
from environment import Environment

LOGGER = logging.getLogger(__name__)

epochs = 100  # number of games
tickers = ['SPY']  # 'AAPL', 'NVDA', 'GOOG', 'INTC'
min_days_to_hold = 5
max_days_to_hold = 15


def main(train, action_bias=0):
    environment = Environment(tickers,
                              initial_deposit=100000,
                              from_date=datetime(2004, 1, 1),
                              to_date=datetime(2010, 1, 1),
                              min_days_to_hold=min_days_to_hold,
                              max_days_to_hold=max_days_to_hold)
    agent = Agent(environment.state_size(),
                  environment.action_size(),
                  epochs=epochs,
                  gamma=0.2,
                  replay_buffer=64,
                  memory_queue_length=32)

    if train:
        for i in range(epochs):
            state = environment.reset()
            done = False

            while not done:
                action = agent.act(state)
                next_state, reward, done = environment.step(action)
                agent.remember(state, action, reward, next_state, done)
                state = next_state
            agent.decrease_epsilon()
            LOGGER.info('Balance for current game: %d', environment.deposit)

        pprint(environment.actions)
        agent.save(environment.main_ticker + '.h5')
    else:
        agent.load(environment.main_ticker + '.h5')

    # Test on!
    test_environment = Environment(tickers,
                                   initial_deposit=100000,
                                   from_date=datetime(2010, 1, 1),
                                   to_date=datetime(2013, 1, 1),
                                   min_days_to_hold=min_days_to_hold,
                                   max_days_to_hold=max_days_to_hold,
                                   scaler=environment.scaler)

    state = test_environment.reset()
    done = False

    while not done:
        action = agent.act(state, False, action_bias)
        next_state, _, done = test_environment.step(action)
        state = next_state
    print_results_on_test_environment(test_environment)
    export_to_file(test_environment.actions)


def print_results_on_test_environment(test_environment):
    LOGGER.info('Balance for current game: %d', test_environment.deposit)
    LOGGER.info(test_environment.actions)
    from collections import Counter
    pos_neg_counter = Counter(['+' if action[1] > 0 else '-' for action in test_environment.actions.values()])
    LOGGER.info(pos_neg_counter)


def export_to_file(actions: dict):
    with open('../actions.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_NONE, lineterminator='\n')
        writer.writerow(['date', 'signal', 'ticker', 'num', 'price'])
        for key, value in actions.items():
            action, reward, deposit_reward, first_day_price, last_day_price, invested_amount = value
            num = int(invested_amount / first_day_price)
            writer.writerow([key.strftime("%Y.%m.%d"), str.upper(action.act), action.ticker, num, first_day_price])


if __name__ == '__main__':
    main(train=True, action_bias=0)  # 0: allow every action; high number: filter
