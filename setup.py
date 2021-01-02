import sys
import os
import fnmatch
import json
import time
import fire
import subprocess

basepath = os.path.dirname(os.path.realpath(__file__))


class ZeroJudgeSetup(object):
    ''' ZeroJudge Setup
    搭配參數如下：
    install: 直接安裝並進行必要設定
    '''

    def __init__(self, offset=1):
        self._offset = offset

    def _exec2(self, cmd):
        print(basepath+"/setup.py EXEC= " + cmd)
        os.system(cmd)

    def _exec(self, cmd):
        print(basepath+"/setup.py EXEC= " + cmd)
        try:
            completed = subprocess.run(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # print('completed:', completed)
        except subprocess.CalledProcessError as err:
            print('CalledERROR:', err)
            return []
        else:
            print('returncode:', completed.returncode)
            print('STDOUT({} bytes): \n{}'.format(len(completed.stdout),
                                                  completed.stdout.decode('utf-8')))
            print('STDERR({} bytes): \n{}'.format(len(completed.stderr),
                                                  completed.stderr.decode('utf-8')))
            return completed.stdout.decode('utf-8').rstrip().split('\n')

    def _pull_tags(self, tmpdir):
        cmd = f'git --git-dir={tmpdir}/.git --work-tree={tmpdir} tag '
        print("cmd=" + cmd)
        tags = subprocess.check_output(cmd.split()).decode(
            'utf-8').rstrip().split('\n')
        count = 0
        for tag in tags:
            print(str(count) + ". tag=" + tag)
            count = count + 1
        tagindex = input("請問要取出哪一個 tag 版本？ ")
        self._exec(
            f'git --git-dir={tmpdir}/.git --work-tree={tmpdir} checkout {tags[int(tagindex)]}')
        open(tmpdir + '/WebContent/META-INF/Version.txt',
             mode='w', encoding='utf-8').write(tags[int(tagindex)])

    def _pull_latestversion(self, tmpdir):
        '''
        取得最新的 tag
        git describe --abbrev=0 --tags
        '''
        cmd = f'git --git-dir={tmpdir}/.git --work-tree={tmpdir} tag '
        taglines = self._exec(cmd)
        print('type(taglines)=', type(taglines), taglines)

        latest_tag = []
        for tagline in taglines:
            tag = [int(x) for x in tagline.split('.')]
            if len(latest_tag) == 0 or latest_tag < tag:
                latest_tag = tag

        latest_tag_line = '.'.join(str(x) for x in latest_tag)
        # cmd = 'git --git-dir=' + tmpdir + '/.git --work-tree=' + \
        #     tmpdir + ' describe --abbrev=0 --tags'
        # latest_tag = self._exec(cmd)

        self._exec(
            f'git --git-dir={tmpdir}/.git --work-tree={tmpdir} checkout -b branch_{latest_tag_line} {latest_tag_line}')
        open(tmpdir + '/WebContent/META-INF/Version.txt',
             mode='w', encoding='utf-8').write(latest_tag_line)

    def install(self, dbpass, dbuser='root', githost='github.com', appname='ZeroJudge', version="latestversion", clean=True, SSL=False):
        gitpath = appname + "_tmp"
        # 更新 v2

        # # 從遠端 pull 回來
        gituri = f"https://{githost}/jiangsir/{appname}"

        # # 放棄本地修改 git --git-dir=ZeroJudge/.git --work-tree=ZeroJudge checkout .
        # self._exec('git --git-dir='+gitpath +
        #            '/.git --work-tree='+gitpath+' checkout .')
        # git --git-dir=ZeroJudge/.git --work-tree=ZeroJudge pull --allow-unrelated-histories https://github.com/jiangsir/ZeroJUdge
        # self._exec('git --git-dir='+gitpath+'/.git --work-tree=' +
        #            gitpath+' pull --allow-unrelated-histories ' + gituri)

        self._exec2(f'git clone {gituri}.git/ {gitpath} --branch master')
        self._exec('rm -rf '+basepath)
        base = basepath[:basepath.rfind('/')]
        self._exec('mv '+base+'/'+gitpath+' '+base+'/' + appname)

        self._exec2(f'sudo python3 {basepath}/setup.py upgradeZeroJudge --dbuser \'{dbuser}\' --dbpass \'{dbpass}\' \
                   --githost \'{githost}\' --version \'{version}\' --clean '+str(clean)+' --SSL ' + str(SSL))

    def upgradeZeroJudge(self, dbpass, warname=None, dbuser='root', githost='github.com', version="latestversion", clean=True, SSL=False):
        ''' 安裝/設定 ZeroJudge 系統 
        '''
        # appname = input("請輸入 git host 上的應用程式名稱: ")  # ex: ZeroJudge
        appname = "ZeroJudge"
        servername = appname+'_Server'
        dbname = appname.lower()

        apptmpdir = os.path.join("/tmp", appname)
        servertmpdir = os.path.join("/tmp", servername)
        self._exec('rm -rf ' + apptmpdir)
        self._exec('mkdir ' + apptmpdir)
        self._exec('rm -rf ' + servertmpdir)
        self._exec('mkdir ' + servertmpdir)
        gituri = f"https://{githost}/jiangsir/{appname}.git {apptmpdir}"
        os.system(f'git clone {gituri}')
        servergituri = f"https://{githost}/jiangsir/{servername}.git {servertmpdir}"
        os.system(f'git clone {servergituri}')

        #choose4 = input("["+appname+"] 請問要取出 1.tag 或者 2. branch：(1, 2) ")
        if version == "latestversion":
            '''
            自動取出最新版
            '''
            self._pull_latestversion(apptmpdir)
            self._pull_latestversion(servertmpdir)

            # self._exec('git --git-dir=' + servertmpdir + '/.git --work-tree=' +
            #            servertmpdir + ' checkout -b branch_'+latest_tag + ' ' + latest_tag)
            # open(servertmpdir + '/WebContent/META-INF/Version.txt',
            #      mode='w', encoding='utf-8').write(latest_tag)

        elif version == "tag":
            self._pull_tags(apptmpdir)
            self._pull_tags(servertmpdir)

            # self._exec('git --git-dir=' + servertmpdir + '/.git --work-tree=' +
            #            servertmpdir + ' checkout ' + tags[int(tagindex)])
            # open(servertmpdir + '/WebContent/META-INF/Version.txt',
            #      mode='w', encoding='utf-8').write(tags[int(tagindex)])
        elif version == "branch":
            cmd = f'git --git-dir={apptmpdir}/.git --work-tree={apptmpdir} branch -a --sort=-committerdate'
            print("cmd=" + cmd)
            branchs = subprocess.check_output(
                cmd.split()).decode('utf-8').rstrip().split('\n')
            count = 0
            for branch in branchs:
                print(str(count) + ". " + branch)
                count = count + 1
            index = input("請問要取出哪一個 app branch？ ")
            branchname = branchs[int(index)].split(
                '/')[len(branchs[int(index)].split('/')) - 1]
            self._exec(
                f'git --git-dir={apptmpdir}/.git --work-tree={apptmpdir} checkout {branchname}')
            cmd = f'git --git-dir={apptmpdir}/.git --work-tree={apptmpdir} show-branch -g'
            message = subprocess.check_output(cmd.split()).decode('utf-8')
            print('message= ' + message)
            open(apptmpdir + '/WebContent/META-INF/Version.txt',
                 mode='w', encoding='utf-8').write(message)
            # ZeroJudge_Server
            cmd = f'git --git-dir={servertmpdir}/.git --work-tree={servertmpdir} branch -a --sort=-committerdate'
            print("cmd=" + cmd)
            branchs = subprocess.check_output(
                cmd.split()).decode('utf-8').rstrip().split('\n')
            count = 0
            for branch in branchs:
                print(str(count) + ". " + branch)
                count = count + 1
            index = input("請問要取出哪一個 server branch？ ")
            branchname = branchs[int(index)].split(
                '/')[len(branchs[int(index)].split('/')) - 1]
            self._exec(
                f'git --git-dir={servertmpdir}/.git --work-tree={servertmpdir} checkout {branchname}')
            cmd = f'git --git-dir={servertmpdir}/.git --work-tree={servertmpdir} show-branch -g'
            message = subprocess.check_output(cmd.split()).decode('utf-8')
            print('message= ' + message)
            open(servertmpdir + '/WebContent/META-INF/Version.txt',
                 mode='w', encoding='utf-8').write(message)

        else:
            print('version 的參數只能為 ("latestversion", "branch", "tag") ')
            sys.exit()

        # 清除所有的 BOM
        for root, dirs, files in os.walk(apptmpdir + "/src/"):
            for file in files:
                if file.endswith(".java"):
                    # print(os.path.join(root, file))
                    s = open(os.path.join(root, file), mode='r',
                             encoding='utf-8-sig').read()
                    open(os.path.join(root, file), mode='w',
                         encoding='utf-8').write(s)

        if warname == None:
            warname = 'ROOT'
        else:
            warname = input(
                "開始打包 war, 請輸入 所要使用的 App Name 。(不輸入則預設為 ROOT.war): ")
            if warname == '':
                warname = 'ROOT'

        for file in os.listdir('/etc/init.d/'):
            if fnmatch.fnmatch(file, 'tomcat*'):
                tomcatN = file
        if clean == True:
            target = 'clean makewar callpy'
        else:
            target = 'makewar callpy'

        self._exec(
            f'ant -f {apptmpdir}/build.xml {target} -Dappname={warname} -DTOMCAT_HOME=/usr/share/{tomcatN}/')
        self._exec(
            f'ant -f {servertmpdir}/build.xml -Dappname={servername} -DTOMCAT_HOME=/usr/share/{tomcatN}/')
        # self._exec("clear")

        while int(subprocess.call(f"mysql -u {dbuser} -p'{dbpass}' -e \"USE {dbname};\"", shell=True)) != 0:
            dbpass = input("輸入資料庫 "+dbuser+" 密碼：")

        self._exec2(
            f"python3 {apptmpdir}/build.py build --warname '{warname}' --dbuser '{dbuser}' --dbpass '{dbpass}' --SSL " + str(SSL))
        self._exec2(
            f"python3 {servertmpdir}/build.py build --warname '{servername}'")


if __name__ == '__main__':
    fire.Fire(ZeroJudgeSetup)
