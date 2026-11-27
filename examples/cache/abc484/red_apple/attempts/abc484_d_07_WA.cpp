#include<bits/stdc++.h>
using namespace std;
#define int long long 
const int N=2e5+5;
int a[N];
int diff[N]; 
int near[N];
signed main(){
	ios::sync_with_stdio(false);
	cin.tie(nullptr);
	//找a_i前1~a_i-1与a_i不同的元素 
	//diff[a_i]=最近相等元素a[t] diff[t]+(a_i-t+1); 
	int n;cin>>n;
	for(int i=1;i<=n;i++){
		cin>>a[i];
	}
	for(int i=1;i<=n;i++){
		if(near[a[i]]==0){
			diff[i]=i;
		}
		else{
			diff[i]=diff[near[a[i]]]+(i-near[a[i]]);
		}
		near[a[i]]=i;
	}
	int ans=0;
	for(int i=1;i<=n;i++){
		if(a[i] != a[i-1])ans+=diff[i];
	}
	cout<<ans;
	return 0;
}