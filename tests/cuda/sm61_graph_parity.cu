// Local P40 qualification. No model, no ISA/SM guard bypass; mutable-buffer CUDA Graph replay vs direct kernels.
#include <cuda_runtime.h>
#include <cstdio>
#include <vector>
__global__ void transform(const float* x,float* y,int n){int i=(int)(blockIdx.x*blockDim.x+threadIdx.x);if(i<n)y[i]=x[i]*2.0f+1.0f;}
int main(){
  cudaDeviceProp prop{};if(cudaGetDeviceProperties(&prop,0)!=cudaSuccess||prop.major!=6||prop.minor!=1){std::puts("SKIP: this qualification targets real sm_61");return 77;}
  const int n=4096;float *x=nullptr,*a=nullptr,*b=nullptr;cudaStream_t stream=nullptr;
  if(cudaMalloc(&x,n*sizeof(float))||cudaMalloc(&a,n*sizeof(float))||cudaMalloc(&b,n*sizeof(float))||cudaStreamCreate(&stream))return 1;
  cudaGraph_t graph=nullptr;cudaGraphExec_t exec=nullptr;
  if(cudaStreamBeginCapture(stream,cudaStreamCaptureModeGlobal)!=cudaSuccess)return 1;
  transform<<<16,256,0,stream>>>(x,b,n);
  if(cudaStreamEndCapture(stream,&graph)!=cudaSuccess||cudaGraphInstantiate(&exec,graph,nullptr,nullptr,0)!=cudaSuccess)return 1;
  std::vector<float> input(n),direct(n),captured(n);
  for(int trial=0;trial<4;++trial){
    for(int i=0;i<n;++i)input[i]=(float)(i+trial*17)/32.0f;
    if(cudaMemcpyAsync(x,input.data(),n*sizeof(float),cudaMemcpyHostToDevice,stream)!=cudaSuccess)return 1;
    transform<<<16,256,0,stream>>>(x,a,n);
    if(cudaGraphLaunch(exec,stream)!=cudaSuccess||cudaStreamSynchronize(stream)!=cudaSuccess)return 1;
    if(cudaMemcpy(direct.data(),a,n*sizeof(float),cudaMemcpyDeviceToHost)!=cudaSuccess||cudaMemcpy(captured.data(),b,n*sizeof(float),cudaMemcpyDeviceToHost)!=cudaSuccess)return 1;
    for(int i=0;i<n;++i)if(direct[i]!=captured[i]||captured[i]!=input[i]*2.0f+1.0f)return 1;
  }
  cudaGraphExecDestroy(exec);cudaGraphDestroy(graph);cudaStreamDestroy(stream);cudaFree(x);cudaFree(a);cudaFree(b);
  std::printf("PASS: %s sm_61 CUDA Graph capture/replay, changed inputs, bitwise direct parity\n",prop.name);return 0;
}
