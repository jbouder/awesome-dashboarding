FROM rilldata/rill:v0.92.1

# The project is copied in, not mounted: Rill writes its DuckDB files into
# the project folder, and edits made in Rill's editor stay in the container.
# No usage analytics from the lab.
RUN mkdir -p /home/rill/.rill && printf 'analytics_enabled: false\n' > /home/rill/.rill/config.yaml
COPY --chown=rill:rill project /home/rill/project
WORKDIR /home/rill/project
EXPOSE 9009
CMD ["start", "/home/rill/project", "--no-open", "--pull-env=false", "--port", "9009"]
