import sys
import json

try:
	import pygit2
except ImportError:
	print 'Error: pygit2 missing'
	sys.exit(1)

config = json.loads(open(sys.argv[1]).read())

GIT_ORIGIN_PREFIX = config['prefix']

developers = {}

repository = pygit2.Repository(config['repo'])

for ref in config['refs']:
	head = repository.lookup_reference('%s%s' % (GIT_ORIGIN_PREFIX, ref))
	
	i = 0

	for commit in repository.walk(head.oid, pygit2.GIT_SORT_TIME):
		if any(rule in commit.message for rule in config['merge']):
			# Skip merges
			continue
		
		diff = commit.tree.diff(commit.parents[0].tree)

		try:
			hunks = diff.changes['hunks']
		except KeyError:
			continue

		for change in hunks:
			if change.old_file != change.new_file:
				continue

			name = change.new_file

			delta = change.old_lines - change.new_lines

			if any(name.startswith(prefix) for prefix in config['watch']) \
				and not any(rule in name for rule in config['ignore']) \
				and any(name.endswith(ext) for ext in config['exts']):

				if delta > 0:
					author = commit.committer.name

					developers.setdefault(author, 0)

					developers[author] += delta

		i += 1

		if i % 100 == 0:
			if config['limit'] is not None:
				print '%.0f%% -- %s/%s processed' % (
					(float(i) / float(config['limit']) * 100),
					i, config['limit']
				)

				if i > config['limit']:
					break
			else:
				print '%s processed...' % i

print
print '-' * 80
print '\tDeveloper\t\t\t\tAdditions'
print '-' * 80
for dev, count in sorted(developers.items(), key=lambda el: el[1], reverse=True):
	print '\t%s\t\t\t\t%s' % (dev, count)

