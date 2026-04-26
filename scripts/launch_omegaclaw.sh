#!/bin/bash
# OmegaClaw IRC Launch Script for Superblock Demo
docker rm -f omegaclaw 2>/dev/null || true
docker run -d \
  --name omegaclaw \
  -e commchannel=irc \
  -e IRC_channel="##superblock-demo-2026" \
  -e IRC_server=irc.quakenet.org \
  -e IRC_port=6667 \
  -e IRC_user=superblock-bot \
  -e provider=ASIOne \
  -e LLM=asi1-ultra \
  -e APIKEY=sk_79a335e9544f49eeb558ae255e9f9690959a453a5f5e46389f9c2ee3fd0a1569 \
  -v omegaclaw-memory:/memory \
  singularitynet/omegaclaw:hackathon2604
echo "OmegaClaw launched!"
