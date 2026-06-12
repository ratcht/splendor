1. Tabular Q-Learning

- Off policy:

Q(S, A) <- Q(S, A) + alpha*[R' + gamma*max_a(Q(S', a)) - Q(S, A)]
S <- S'

2. SARSA

- On policy:

Q(S, A) <- Q(S, A) + alpha*[R' + gamma*Q(S', A') - Q(S, A)]
S <- S', A <- A'

3. Deep Q-Network
4. REINFORCE
5. PPO