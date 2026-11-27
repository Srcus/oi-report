#include<bits/stdc++.h>
using namespace std;
int main(){
	int k;cin>>k;
	bool flag=false;
	int ans=10;
	for(int i=1;i<=k;i++){
		int x;cin>>x;
		if(x==9)flag=true;
		ans=min(ans,x);
	}
	if(flag)cout<<ans;
	else cout<<-1;
	return 0;
}