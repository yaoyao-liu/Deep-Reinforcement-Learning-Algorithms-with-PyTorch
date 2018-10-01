import torch
import torch.nn.functional as F
from DQN_Agents.DDQN_Agent import DDQN_Agent
from Utilities.Data_Structures.Prioritised_Replay_Buffer import Prioritised_Replay_Buffer


class DDQN_With_Prioritised_Experience_Replay(DDQN_Agent):


    def __init__(self, environment, seed, hyperparameters, rolling_score_length,
                 average_score_required, agent_name):
        DDQN_Agent.__init__(self, environment=environment,
                            seed=seed, hyperparameters=hyperparameters, rolling_score_length=rolling_score_length,
                            average_score_required=average_score_required, agent_name=agent_name)

        self.memory = Prioritised_Replay_Buffer(hyperparameters, seed)

    def learn(self):
        sampled_experiences, importance_sampling_weights = self.memory.sample()
        states, actions, rewards, next_states, dones = sampled_experiences
        loss, td_errors = self.compute_loss_and_td_errors(states, next_states, rewards, actions, dones, importance_sampling_weights)

        self.take_optimisation_step(loss)
        self.soft_update_of_target_network()
        self.memory.update_td_errors(td_errors.squeeze(1))

    def save_experience(self):
        """Saves the latest experience including the td_error"""
        max_td_error_in_experiences = self.memory.give_max_td_error() + 1e-9
        self.memory.add_experience(max_td_error_in_experiences, self.state, self.action, self.reward, self.next_state, self.done)

    def compute_loss_and_td_errors(self, states, next_states, rewards, actions, dones, importance_sampling_weights):
        """Calculates the loss for the local Q network. It weighs each observations loss according to the importance
        sampling weights which come from the prioritised replay buffer"""
        Q_targets = self.compute_q_targets(next_states, rewards, dones)
        Q_expected = self.compute_expected_q_values(states, actions)
        loss = F.mse_loss(Q_expected, Q_targets)
        loss = loss * importance_sampling_weights
        loss = torch.mean(loss)

        td_errors = Q_targets.data.cpu().numpy() - Q_expected.data.cpu().numpy()

        return loss, td_errors