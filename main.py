import os
import threading
import time
import tensorflow as tf
from absl import app
from absl import flags
from pysc2.env import run_loop
from pysc2.env import sc2_env

from a3c_agent import A3CAgent
from a3c_agent import A3C_SCREEN_SIZE_X, A3C_SCREEN_SIZE_Y, PARALLEL_THREADS, SAVE_PATH,\
    LOG_PATH, TRAINING


flags.DEFINE_string("agent", "a3c", "Which agent to run.")

"""Script for starting all agents (a3c, very simple and slightly smarter).

This scripts is the starter for all agents, it has one command line parameter (--agent), that denotes which agent to run.
By default it runs the A3C agent.
"""

def run_thread(agent, ssize_x, ssize_y, msize_x, msize_y, display=False):
    """Runs an agent thread.

    This helper function creates the evironment for an agent and starts the main loop of one thread.

    :param agent: agent to run
    :param ssize_x: X-size of the screen
    :param ssize_y: Y-size of the screen
    :param msize_x: X-size of the minimap
    :param msize_y: Y-size of the minimap
    :param display: whether to display the pygame output of an agent, for performance reasons deactivated by default
    """
    with sc2_env.SC2Env(map_name='CollectMineralsAndGas',
                        agent_race='T',
                        difficulty=None,
                        step_mul=8,
                        game_steps_per_episode=0,
                        screen_size_px=(ssize_x, ssize_y),
                        minimap_size_px=(msize_x, msize_y),
                        visualize=display) as env:

        run_loop.run_loop([agent], env)


def start_a3c_agent():
    """Starts the A3C agent.

    Helper function for setting up the A3C agents. If it is in training mode it starts PARALLEL_THREADS agents, otherwise
    it will only start one agent. It creates the TensorFlow session and TensorFlow's summary writer. If it is continuing
    a previous session and can't find an agent instance, it will just ignore this instance. It also initialises the
    weights of the neural network, if it doesn't find a previously saved one and initialises it. If it should show the
    pygame output of an agent, it only shows it for the first instance. Most of it's behaviour can be controlled with
    the same constants that can be found in a3c_agent.py and are also used by the A3C agent.
    """
    summary_writer = tf.summary.FileWriter(LOG_PATH)

    if not TRAINING:
        parallel = 1
    else:
        parallel = PARALLEL_THREADS


    # MANNSI sync version
    # with tf.Session() as session:
    #    agent = A3CAgent(session, 0, summary_writer)
    #    session.run(tf.global_variables_initializer())  # This used to be in the agent initialize method.
    #    run_thread(agent, A3C_SCREEN_SIZE_X, A3C_SCREEN_SIZE_Y, A3C_MINIMAP_SIZE_X, A3C_MINIMAP_SIZE_Y, False)
    # return

    with tf.Session() as session:
        agents = []
        for i in range(parallel):
            agent = A3CAgent(session, i, summary_writer)
            if os.path.exists(SAVE_PATH):
                if agent.load_checkpoint():
                    agents.append(agent)
            else:
                agents.append(agent)

        session.run(tf.global_variables_initializer())  # This used to be in the agent initialize method.
        threads = []
        for agent in agents:
            thread_args = (agent, A3C_SCREEN_SIZE_X, A3C_SCREEN_SIZE_Y, A3C_SCREEN_SIZE_X, A3C_SCREEN_SIZE_Y, False)
            t = threading.Thread(target=run_thread, args=thread_args)
            threads.append(t)
            t.start()
            time.sleep(5)
        for t in threads:
            t.join()


def main(argv):
    """Main function.

    This function check which agent was specified as command line parameter and launches it.

    :param argv: empty
    :return:
    """
    start_a3c_agent()


if __name__ == '__main__':
    print('Starting...')
    app.run(main)
