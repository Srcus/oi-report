#include<bits/stdc++.h>
using namespace std;
#define int long long
const int N=1e5+5;
int n;
vector<int>a;vector<int>b;
bool check1(int l,int r){
	for(int i=l;i<=r;i++){
		if(i==r){
			if(a[i]!=b[l])return false;
		}
		else{
			if(a[i]!=b[i+1])return false;
		}
	}
	return true;
}
bool check2(int l,int r){
	for(int i=l;i<=r;i++){
		if(i==l){
			if(a[i]!=b[r])return false;
		}
		else{
			if(a[i]!=b[i-1])return false;
		}
	}
	return true;
}
signed main(){
	ios::sync_with_stdio(false);
	cin.tie(nullptr);
	cin>>n;
	a.resize(n+1);b.resize(n+1);
	for(int i=1;i<=n;i++){
		cin>>a[i];
	}
	for(int i=1;i<=n;i++){
		cin>>b[i];
	}
	vector<int>cnt(n+1);
	for(int i=1;i<=n;i++){
		cnt[a[i]]++;
	} 
	for(int i=1;i<=n;i++){
		cnt[b[i]]--;
	}
	bool flag=true;
	for(int i=1;i<=n;i++){
		if(cnt[i]!=0) {
			flag=false;
			break;
		}
	}
	if(!flag){
		cout<<"No"<<endl;
		return 0;
	}
	if(a==b){
		cout<<"Yes"<<endl;
		return 0;
	} 
	int l=1;int r=n;
	int flag1=true;
	int flag2=true;
	while(l<r){
		if(a[l]==b[l]&&flag1)l++;
		if(a[l]!=b[l])flag1=false;
		if(a[r]==b[r]&&flag2)r--;
		if(a[r]!=b[r])flag2=false;
		if(!flag2&&!flag1)break;
	}
	if(check1(l,r)||check2(l,r))cout<<"Yes"<<endl;
	else cout<<"No";
	return 0;
} 
