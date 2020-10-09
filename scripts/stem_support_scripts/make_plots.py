import os
import sys
import matplotlib.pyplot as plt 
import pandas as pd 
import numpy as np 
import json
import glob 
import seaborn as sns
class MakePlots(): 
	"""A class to make plots."""
	def __init__(self,input_csv,plot_fields,file_list1,file_list2,file_list3): 

		self.input_csv=input_csv
		self.plot_fields=plot_fields
		self.file_list1 = file_list1
		self.file_list2 = file_list2
		self.file_list3 = file_list3
		

	def check_field(self,filename): 
		print(f'filename is: {filename}')
		try: 
			if filename == None: 
				file='null_value'

			elif self.input_csv ==None: 
				self.input_csv = 'null_value'
			if ('one' in self.input_csv) or ('one' in filename): 
				category = 'one'
			elif ('two' in self.input_csv) or ('two' in filename): 
				category = 'two'
			elif ('three' in self.input_csv) or ('three' in filename): 
				category = 'three'
			else: 
				#print('double check your inputs')
				category = 'null_value'
			return category
		except: 
			pass
	def make_hist(self): 
		df = pd.read_csv(self.input_csv)
		print(df.head())
		print(self.plot_fields)
		category = self.check_field(self.input_csv,None)
		fig,ax = plt.subplots(1,2)
		ax = ax.flatten()
		colors = ['darkblue','darkred']
		for i in range(len(self.plot_fields)): 
			# print(f'count is: {i}')
			# print(f'i is: {i}')
			# print(df[self.plot_fields[i]])
			# print(pd.Series(self.plot_fields[i]).value_counts())
			df[self.plot_fields[i]] = df[self.plot_fields[i]].str.strip()
			df[self.plot_fields[i]] = df[self.plot_fields[i]].str.lower()
			ax[i]=pd.Series(df[self.plot_fields[i]]).value_counts().plot(kind='bar',color=colors[i])
			ax[i].set_xlabel(self.plot_fields[i]);ax[i].set_ylabel('count')
			ax[i].set_title(f'Uncertainty category {category} distributions') 
			if self.plot_fields[i].lower() == 'class': 
				ax[i].annotate(f'n = {df[self.plot_fields[i]].count()}',xy=(0.8,0.8),xycoords='figure fraction')
			else: 
				plt.xticks(rotation=45)
		plt.show()
		plt.close('all')

	def make_line(self,nrows,ncols): 
		
		uncertainty_dict = {'one':'low','two':'medium','three':'high'}
		fig,ax = plt.subplots(nrows,ncols,constrained_layout=True,sharex=True)

		ax = ax.flatten()
		count = 0
		for file1,file2,file3 in zip(self.file_list1,self.file_list2,self.file_list3): #list of file paths
			try: 
				df1 = pd.read_csv(file1)
				df2 = pd.read_csv(file2)
				df3 = pd.read_csv(file3)
				#print(df)
				filename = os.path.split(file1)[1]
				#print(f'the filename here is now: {filename} and it is type {type(filename)}')
				category = 'null_value'#self.check_field(filename)
				if not category in uncertainty_dict.keys(): #convert the pixel counts to areas for that national parks
					df1 = df1*900
					df2 = df2*900
					df3 = df3*900
					#print('scaled df is: ',df1)
				else: 
					pass
				#change all values into square kms instead of square meters
				df1 = df1/1000000
				df2 = df2/1000000
				df3 = df3/1000000
				for column1,column2,column3 in zip(df1.columns,df2.columns,df3.columns): #get rid of non-year cols 
					try: 
						int(column1)
					except ValueError:
						print('col was not a year col, dropping')
						df1=df1.drop(columns=[column1])
						df2=df2.drop(columns=[column2])
						df3=df3.drop(columns=[column3])
				plot_df1 = df1.T.reset_index().rename(columns={'index':'year',0:'area'})
				plot_df2 = df2.T.reset_index().rename(columns={'index':'year',0:'area'})
				plot_df3 = df3.T.reset_index().rename(columns={'index':'year',0:'area'})
				#plot_df['plus_two_std'] = plot_df.area+(plot_df.area.std()*2)
				#plot_df['minus_two_std'] = plot_df.area-(plot_df.area.std()*2) 
				sns.lineplot(data=plot_df1,x='year',y='area',ax=ax[count],color='darkred',label='NDSI NLCD 2001',legend=False)#.plot(df.T)
				sns.lineplot(data=plot_df2,x='year',y='area',ax=ax[count],color='darkblue',label='TCB NLCD 2001',legend=False)#.plot(df.T)
				sns.lineplot(data=plot_df3,x='year',y='area',ax=ax[count],color='green',label='NDSI NLCD 2016',legend=False)#.plot(df.T)

				#ax[count].fill_between(plot_df['year'], plot_df['plus_two_std'], plot_df['minus_two_std'], color='darkred', alpha=.1)
				ax[count].tick_params(axis='x', rotation=90)
				ax[count].set_ylabel(' ')
				ax[count].set_xlabel(' ')

				#ax[count].set_ylabel('Glacier covered area (sqare km')
				if not category == 'null_value':
					ax[count].set_title(f'{(uncertainty_dict[str(category)]).title()} level of certainty')
				else: # " ".join(["John", "Charles", "Smith"])
					ax[count].set_title(" ".join(filename[:-4].split('_')).title())
				fig.text(0.002, 0.5, 'Glacier covered area (square km)', va='center', rotation='vertical')
				#plt.setp(ax[:, 0], ylabel='Glacier covered area (square km)')

				count += 1 
			except IndexError: 
				print('IndexError')
				continue 
			#ax[count].set_xticks(rotation=90)
		#plt.tight_layout()
		#plt.legend()
		ax[nrows-1].legend()
		plt.show()
		plt.close('all')


		
def main(): 
	params = sys.argv[1]
	with open(str(params)) as f:
		variables = json.load(f)
		csv_dir= variables["csv_dir"]
		#plot_fields = list(variables['plot_fields'])
		plot_fields = variables['plot_fields']
		#print(type(plot_fields))
	# for file in glob.glob(csv_dir+'*.csv'): 
	# 	plots = MakePlots(file,plot_fields,None)
	# 	plots.make_hist()

	regional_list = []
	np_list = []
	#make both regional and national park plots
	# for file in glob.glob(csv_dir+'*one_.csv'): 
	# 	print(f'file is: {file}')
	# 	category = MakePlots(file,None,None).check_field('null_value') #tells us if this is regional or nps
		#print(f'category is: {category}')
	# 	if not category == 'null_value': 
	# 		regional_list.append(file)
	# 	else: 
	# 		np_list.append(file)
	# print(np_list)
	# ["class", "image_source"]   
	#print('regional list is', regional_list)
	#print('np list is', np_list)
	#MakePlots(None,None,regional_list).make_line(1,3) #just plots for the three certainty levels
	ndsi_nlcd_2001 = glob.glob(csv_dir+'*two_corrected.csv')
	ndsi_nlcd_2016 = glob.glob(csv_dir+'*two_2016_nlcd.csv')
	tcb_nlcd_2001 = glob.glob(csv_dir+'*two_tcb.csv')

	ndsi_nlcd_2001 = sorted([x for x in ndsi_nlcd_2001 if not ('alagnak' in x or 'aniakchak' in x or 'katmai_national_preserve' in x or 'glacier_bay_national_preserve' in x)]) #[i for i in sents if not ('@$\t' in i or '#' in i)]
	ndsi_nlcd_2016 = sorted([x for x in ndsi_nlcd_2016 if not ('alagnak' in x or 'aniakchak' in x or 'katmai_national_preserve' in x or 'glacier_bay_national_preserve' in x)]) 
	tcb_nlcd_2001 = sorted([x for x in tcb_nlcd_2001 if not ('alagnak' in x or 'aniakchak' in x or 'katmai_national_preserve' in x or 'glacier_bay_national_preserve' in x)])
	# for file1,file2 in zip(ndsi_nlcd_2001,tcb_nldc_2001): 
	# 	if ('alagnak' in file1) or ('aniakchak' in file1) or ('katmai_national_preserve' in file1) or ('glacier_bay_national_preserve' in file1): 
	# 		print('No stats or no glaciers for that park for file1, skipping')
	# 	elif ('alagnak' in file2) or ('aniakchak' in file2) or ('katmai_national_preserve' in file2) or ('glacier_bay_national_preserve' in file2): 
	print(ndsi_nlcd_2001)
	print(tcb_nlcd_2001)
	MakePlots(None,None,ndsi_nlcd_2001,tcb_nlcd_2001,ndsi_nlcd_2016).make_line(3,3)
	#MakePlots(None,None,np_list).make_line(3,3)
if __name__ == '__main__':
	main()

# df = pd.read_csv(self.input_csv)
# 		df[self.plot_field] = df[self.plot_field].str.strip()
# 		df[self.plot_field] = df[self.plot_field].str.lower()
# 		ax=pd.Series(df[self.plot_field]).value_counts().plot(kind='bar',color='darkred')
# 		ax.set_xlabel(self.plot_field);ax.set_ylabel('count')
# 		ax.set_title(f'Uncertainty category {self.modifier} distributions') 
# 		if self.plot_field.lower() == 'class': 
# 			ax.annotate(f'n = {df[self.plot_field].count()}',xy=(0.8,0.8),xycoords='figure fraction')
# 		else: 
# 			plt.xticks(rotation=45)

# 		plt.show()
# 		plt.close('all')

# colors = ['darkblue','darkred']
# 		for i in range(len(self.plot_fields)): 
# 			print(f'count is: {i}')
# 			print(f'i is: {i}')
# 			print(df[self.plot_fields[i]])

# 			df[self.plot_fields[i]] = df[self.plot_fields[i]].str.strip()
# 			df[self.plot_fields[i]] = df[self.plot_fields[i]].str.lower()
# 			ax[i]=pd.Series(self.plot_fields[i]).value_counts().plot(kind='bar',color=colors[i])
# 			ax[i].set_xlabel(self.plot_fields[i]);ax[i].set_ylabel('count')
# 			ax[i].set_title(f'Uncertainty category {category} distributions') 
# 			if self.plot_fields[i].lower() == 'class': 
# 				ax[i].annotate(f'n = {df[self.plot_fields[i]].count()}',xy=(0.8,0.8),xycoords='figure fraction')
# 			else: 
# 				plt.xticks(rotation=45)


# df = pd.read_csv(self.input_csv)
# 		if 'one' in self.input_csv: 
# 			category = 'one'
# 		elif 'two' in self.input_csv: 
# 			category = 'two'
# 		elif 'three' in self.input_csv: 
# 			category = 'three'
# 		else: 
# 			print('double check your inputs')
# 			category = 'null'
# 		fig,ax = plt.subplots(2)
# 		#ax = ax.flatten()

# 		df[self.plot_fields[0]] = df[self.plot_fields[0]].str.strip()
# 		df[self.plot_fields[0]] = df[self.plot_fields[0]].str.lower()
# 		ax[0]=pd.Series(df[self.plot_fields[0]]).value_counts().plot(kind='bar',color='darkred')
# 		ax[0].set_xlabel(self.plot_fields[0]);ax[0].set_ylabel('count')
# 		ax[0].set_title(f'Uncertainty category {category} distributions')  
# 		ax[0].annotate(f'n = {df[self.plot_fields[0]].count()}',xy=(0.8,0.8),xycoords='figure fraction')
		
# 		df[self.plot_fields[1]] = df[self.plot_fields[1]].str.strip()
# 		df[self.plot_fields[1]] = df[self.plot_fields[1]].str.lower()
# 		ax[1]=pd.Series(df[self.plot_fields[1]]).value_counts().plot(kind='bar',color='darkblue')
# 		ax[1].set_xlabel(self.plot_fields[1]);ax[1].set_ylabel('count')
# 		ax[1].set_title(f'Uncertainty category {category} distributions')  
# 		ax[1].annotate(f'n = {df[self.plot_fields[1]].count()}',xy=(0.8,0.8),xycoords='figure fraction')
# 		plt.xticks(rotation=45)
# 		plt.show()
# 		plt.close('all')

# def make_line(self,nrows,ncols): 
		
# 		uncertainty_dict = {'one':'low','two':'medium','three':'high'}
# 		fig,ax = plt.subplots(nrows,ncols,constrained_layout=True,sharex=True)

# 		ax = ax.flatten()
# 		count = 0
# 		for file in self.file_list: #list of file paths
# 			print(f'file is: {file}')
# 			if ('alagnak' in file) or ('aniakchak' in file) or ('katmai_national_preserve' in file) or ('glacier_bay_national_preserve' in file): 
# 				print('No stats or no glaciers for that park, skipping')
# 			else: 	
# 				try: 
# 					df = pd.read_csv(file)
# 					#print(df)
# 					filename = os.path.split(file)[1]
# 					#print(f'the filename here is now: {filename} and it is type {type(filename)}')
# 					category = 'null_value'#self.check_field(filename)
# 					if not category in uncertainty_dict.keys(): #convert the pixel counts to areas for that national parks
# 						df = df*900
# 						print('scaled df is: ',df)
# 					else: 
# 						pass
# 					#change all values into square kms instead of square meters
# 					df = df/1000000
# 					#print('df is now: ', df)
# 					#print(df.T)
# 					#print(f'the function category is: {category}')
# 					for column in df.columns: #get rid of non-year cols 
# 						try: 
# 							int(column)
# 						except ValueError:
# 							print('col was not a year col, dropping')
# 							df=df.drop(columns=[column])
# 					plot_df = df.T.reset_index().rename(columns={'index':'year',0:'area'})
# 					#plot_df['plus_two_std'] = plot_df.area+(plot_df.area.std()*2)
# 					#plot_df['minus_two_std'] = plot_df.area-(plot_df.area.std()*2) 
# 					sns.lineplot(data=plot_df,x='year',y='area',ax=ax[count],color='darkred')#.plot(df.T)
# 					#ax[count].fill_between(plot_df['year'], plot_df['plus_two_std'], plot_df['minus_two_std'], color='darkred', alpha=.1)
# 					ax[count].tick_params(axis='x', rotation=90)
# 					ax[count].set_ylabel(' ')
# 					ax[count].set_xlabel(' ')

# 					#ax[count].set_ylabel('Glacier covered area (sqare km')
# 					if not category == 'null_value':
# 						ax[count].set_title(f'{(uncertainty_dict[str(category)]).title()} level of certainty')
# 					else: # " ".join(["John", "Charles", "Smith"])
# 						ax[count].set_title(" ".join(filename[:-4].split('_')).title())
# 					fig.text(0.001, 0.5, 'Glacier covered area (square km)', va='center', rotation='vertical')
# 					#plt.setp(ax[:, 0], ylabel='Glacier covered area (square km)')


# 					count += 1
# 				except IndexError: 
# 					print('IndexError')
# 					continue 
# 			#ax[count].set_xticks(rotation=90)
# 		#plt.tight_layout()
# 		plt.show()
# 		plt.close('all')