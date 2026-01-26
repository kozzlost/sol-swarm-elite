# 🚀 $AGENT Token Creation Guide - Pump.fun

## Step 1: Go to Pump.fun

Open: **https://pump.fun/create**

Connect your Solana wallet (Phantom, Solflare, etc.)

---

## Step 2: Fill Token Details

| Field | Value |
|-------|-------|
| **Name** | Swarm Elite Agent |
| **Ticker** | AGENT |
| **Description** | AI-powered trading swarm with 100 autonomous agents. 2% fees fund the bots, infrastructure, development, and builders. The more $AGENT trades, the smarter the swarm becomes. 🤖🐝 |

### Image
Use an AI-generated robot/swarm image or create one at:
- DALL-E / Midjourney
- Or use: https://lexica.art (search "robot swarm")

### Social Links (Optional)
| Field | Value |
|-------|-------|
| Twitter | Your handle |
| Telegram | Your group (if any) |
| Website | github.com/kozzlost/sol-swarm-elite |

---

## Step 3: Launch

1. Click **"Create Coin"**
2. Confirm the transaction in your wallet
3. **COPY THE MINT ADDRESS** - You'll need this!

---

## Step 4: Update Your Config

After creation, update your `.env`:

```env
AGENT_TOKEN_MINT=<paste_your_mint_address_here>
```

---

## Step 5: Initial Liquidity (Optional but Recommended)

Add 0.5-1 SOL initial liquidity to:
- Make the token tradeable
- Show commitment to the project
- Attract early traders

---

## Step 6: Marketing Checklist

- [ ] Tweet the launch with contract address
- [ ] Post in Solana trading groups
- [ ] Create a Telegram group
- [ ] Update README with token address
- [ ] Pin the contract on your Twitter

---

## Sample Launch Tweet

```
🤖 $AGENT is LIVE on @pumpdotfun

AI trading swarm with 100 autonomous agents
• 2% fees fund the bots automatically
• More trading = smarter swarm
• Open source: github.com/kozzlost/sol-swarm-elite

CA: [YOUR_MINT_ADDRESS]

The flywheel begins 🔄
```

---

## Fee Distribution Reminder

Every $AGENT trade generates 2% fees:
- 25% → Bot Trading Treasury (funds the AI)
- 25% → Infrastructure (servers/APIs)
- 25% → Development (future features)
- 25% → Builder Income (you!)

Your wallets are already configured in `.env`

---

## After Launch

1. Start the swarm: `streamlit run main.py`
2. Watch fees accumulate in the dashboard
3. Spawn agents as treasury grows
4. Let the flywheel spin 🔄

---

## ⚠️ Important Reminders

- 90%+ of pump.fun tokens go to zero
- Don't overpromise - be honest about risks
- Never share your wallet private keys
- This is research/educational software
- NFA / DYOR

Good luck! 🚀
