#include<stdio.h>

char str[10000005];

int main()
{
	FILE *fpin,*fpout;
	fpin=fopen("classdata.raw","r");
	fpout=fopen("classdata.json","w");

	fgets(str,10000000,fpin);
	char *p=str+1;
	char id[30],no[30];
	fprintf(fpout,"{");
	int flag=0;
	while(*p) {
	    if(*p=='d' && *(p-1) =='i') {
	        p+=2;
	        char *pid;
	        for(pid=id;*p!=',';p++,pid++)
	            *pid=*p;
	        *pid='\0';
	    }
	    if(*p=='o' && *(p-1)=='n') {
	    	p+=3;
	    	char *pno;
	        for(pno=no;*p!='\'';p++,pno++)
	            *pno=*p;
	        *pno='\0';
	        if(flag)
	            fprintf(fpout,", ");
	        flag=1;
	        fprintf(fpout,"\"%s\":\"%s\"",no,id);
	    }
	    p++;
	}
	fprintf(fpout,"}");
	fclose(fpout);
	return 0;
}


