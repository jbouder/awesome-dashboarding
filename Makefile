# The dashboard lab. Every target calls scripts/lab.sh.
#
# Get started
#   make doctor               check Docker, memory, ports, and tools
#   make env                  create .env from .env.example
#   make pull                 download every image ahead of time
#   make up all               start every stack with the seed data loaded
#   make up superset grafana  start some stacks
#
# Use the lab
#   make list                 every stack, its type, URL, and license
#   make status               each stack's state and whether its URL responds
#   make open superset        open stacks in the browser (or: make open all)
#   make story                the questions to ask every tool, and the answer
#   make incident             3 minutes of errors on checkout, for Grafana's alert
#   make incident payments latency 5
#   make psql                 a read-only psql shell on the warehouse
#   make sql Q="SELECT count(*) FROM shop.orders"
#
# Manage it
#   make smoke                check the running stacks work and agree
#   make stop metabase        stop stacks, leave the rest running
#   make restart superset     stop and start stacks again
#   make logs superset        follow a stack's logs
#   make ps                   every lab container
#   make down                 stop everything, keep the data
#   make reset                stop everything and delete all data
#   make reseed               regenerate the seed data
#   make lint                 lint the lab's own scripts and Compose files

LAB := ./scripts/lab.sh
ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

# Commands whose following words are arguments, not targets.
ARG_COMMANDS := up stop restart open pull incident logs

.PHONY: help doctor env pull list up stop restart status open smoke story \
	psql sql incident logs ps down reset reseed lint

help:
	@sed -n '3,29p' Makefile | sed 's/^# \{0,1\}//'

doctor env list status smoke story psql ps down reset reseed lint:
	@$(LAB) $@

up stop restart open pull incident logs:
	@$(LAB) $@ $(ARGS)

sql:
	@$(LAB) sql "$(Q)"

ifneq ($(filter $(ARG_COMMANDS),$(firstword $(MAKECMDGOALS))),)
%:
	@:
endif
