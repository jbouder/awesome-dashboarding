# The dashboard lab. Every target calls scripts/lab.sh.
#
#   make list                 every stack, its type, URL, and license
#   make up superset grafana  start stacks with the seed data loaded
#   make up all               start every stack
#   make down                 stop everything, keep the data
#   make reset                stop everything and delete all data
#   make reseed               regenerate the seed data
#   make incident             start a 3-minute error incident on checkout
#   make incident payments latency 5
#   make ps                   what is running
#   make logs superset        follow a stack's logs

LAB := ./scripts/lab.sh
ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

.PHONY: help list up down reset reseed incident ps logs

help:
	@sed -n '3,13p' Makefile | sed 's/^# \{0,1\}//'

list:
	@$(LAB) list

up:
	@$(LAB) up $(ARGS)

down:
	@$(LAB) down

reset:
	@$(LAB) reset

reseed:
	@$(LAB) reseed

incident:
	@$(LAB) incident $(ARGS)

ps:
	@$(LAB) ps

logs:
	@$(LAB) logs $(ARGS)

# Words after up, incident, or logs are arguments, not targets.
ifneq ($(filter up incident logs,$(firstword $(MAKECMDGOALS))),)
%:
	@:
endif
