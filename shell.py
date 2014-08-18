import os
import shlex
import sys
import subprocess

class job():
	pid = 0
	job_number = 0
	command = None

	def __init__(self,pid,job_number,command):
		self.pid = pid
		self.job_number = job_number
		self.command = command


class PShell():
	home = os.getcwd()

	historyList = []
	historyCommand = []
	jobsList = []

	amper = False
	redirected = False

	jobCount = 1
	def r_loop(self):
		while True:
			print(len(self.jobsList))
			if(len(self.jobsList)>0):
				for check in self.jobsList:
					done = os.waitpid(check.pid,os.WNOHANG)

					if(done[0] > 0):
						prompt = "<Done>	%s" % (check.command)
						print(prompt)
						self.jobsList.pop(self.jobsList.index(check))

			#Get the new input from either the terminal or the history list
			if(len(self.historyCommand)==0):
				prompt = "[%s@%s %s]>> " % \
					(os.getlogin(),
					os.uname()[1],
					os.path.basename(os.getcwd()))
				line = input(prompt)
				self.redirected = not os.isatty(sys.stdin.fileno())
				if(self.redirected):
					print (line)

			else:
				line = self.historyCommand[0]
				self.historyCommand.pop()
				self.historyList.pop()

			words = self.word_list(line)
			if(len(words)>0):
				command = words[0]

			if(len(self.historyList)<10):
				self.historyList.append(line)
			else:
				self.historyList.pop(0)
				self.historyList.append(line)

			if ("&" in words):
				amper = True
				words.pop()
			else:
				amper = False

			if(len(words)>0):
				try:
					child = os.fork()
					if child == 0: # we are in the child
						if ("|" in words):
							if( not self.syntax_check(words)):
								print("That syntax isn't valid for the pipe!")
							else:
								while ("|" in words):
									r, w = os.pipe()
									index_of_pipe = words.index("|")

									if (os.fork() == 0):
										os.dup2(w, 1)
										os.close(r)
										os.execvp(command, words[0:index_of_pipe])

									words = words[index_of_pipe+1:]
									
									if ("|" in words): 
										index_of_pipe = words.index("|")
									else: 
										index_of_pipe = len(words)
									
									os.dup2(r, 0)
									os.close(w)

								command = words[0]
								os.execvp(command, words[0:index_of_pipe])
						elif(command == "cd"):
							self.cd(words)
						elif(command == "pwd"):
							self.pwd()
						elif((command == "history") or (command == "h")):
							self.history(words)
						elif(command == "jobs"):
							self.jobs(words)
						else:
							os.execvp(command, words)
					else:
						if(not amper):
							os.waitpid(child, 0)
						else:
							os.waitpid(child,os.WNOHANG)
							if(len(self.jobsList) == 0):
								self.jobCount = 1
							else:
								self.jobCount = (self.jobsList[-1].job_number) + 1

							child_job = job(child, self.jobCount, line)
							self.jobsList.append(child_job)
							print( "[%s]	%s " % (self.jobCount,child))
							self.jobCount += 1

				except OSError:
					print('Caught an OSError.')

	def word_list(self, line):
		"""Break the line into shell words."""
		lexer = shlex.shlex(line, posix=True)
		lexer.whitespace_split = False
		lexer.wordchars += '#$+-,./?@^='
		words = list(lexer)
		return words

	def pwd(self):
		print(os.getcwd())

	def cd(self, words):
		try:
			if(len(words)>1):
				dir = words[1].replace('~',self.home)
				os.chdir(dir)
			else:
				print("Please put a directory to cd into")
		except FileNotFoundError:
			print ("That directory doesn't seem to exist")

	def history(self, words):
		if(len(words) == 1):
			for i in range(0,len(self.historyList)):
				listItem = "%s: %s" % (i+1,self.historyList[i])
				print(listItem)
		else:
			if(int(words[1]) <= 10):
				self.historyCommand.append(self.historyList[(int(words[1])-1)])
			else:
				print("Ae MAN, We only know the 10 commandments")

	def syntax_check(self,words):

		if((words[0] == "|") or (words[-1] == "|")):
			return False

		for x in range (0,len(words) - 1):
			if((words[x] is "|") and (words[x+1] is "|")):
				return False

		return True

	def jobs(self,words):
		for job in self.jobsList:
			#get the job status
			pid = job.pid
			ps = subprocess.Popen(['ps','-p', str(pid), '-o','state='], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			result,error = ps.communicate()
			if result.decode() != '':
				print('[{}] <{}> {}'.format(job.job_number, result.decode()[0],job.command))

def main():
	try:
		my_shell = PShell()
		my_shell.r_loop()

	except EOFError:
		sys.exit()
	except KeyboardInterrupt:
		sys.exit()

if __name__ == '__main__':
	main()


