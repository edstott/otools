close all;
min_contourlength = 40;
max_smooth_window = 100;
smooth_span = 29;
gradient_smooth = 9;    %Window size for gradient map smoothing
smooth_mode = 'grad';
gradient_win_factor = 20E-3;    %Inverse gradient to window size coefficient
window_exp = floor(max_smooth_window/2)+1;

%Initialise OSM output
docNode = com.mathworks.xml.XMLUtils.createDocument('osm');
root = docNode.getDocumentElement;
root.setAttribute('version','0.6');
root.setAttribute('generator','edcontour');

noderoot = docNode.createElement('tocitem');
wayroot = docNode.createElement('tocitem');
idcount = 0;


if mod(smooth_span,2) == 0
    smooth_span = smooth_span + 1;
    disp('smooth_span must be odd, added 1');
end
if smooth_span > min_contourlength
     min_contourlength = smooth_span;
    disp('smooth_span must not be greater than min_contourlength, increased min_contourlength');
end
loopovr = (smooth_span-1)/2;

%Calculate gradient matrix
[gradx,grady] = gradient(hdata);
grad = (gradx.^2+grady.^2).^0.5;
grad = conv2(grad,ones(gradient_smooth)/gradient_smooth^2,'same');
grad(grad==0) = 0.001;  %Eliminate points with zero gradient
winsize = gradient_win_factor.*max_smooth_window./grad;
winsize(winsize>max_smooth_window) = max_smooth_window;

%Get length and index of each contour
i = 1;
j = 1;
contourlength = zeros(length(contours),2);
while i<length(contours)
    contourlength(j,:) = [contours(2,i),i];
    i = i + contourlength(j) + 1;
    j = j + 1;
end
contourlength = contourlength(1:find(contourlength == 0,1,'first')-1,:);
ncontours = length(contourlength);

%Get indices of long and short contours
i_longcontours = contourlength(:,1)>=min_contourlength;
i_longcontours = find(i_longcontours);
i_shortcontours = contourlength(:,1)<min_contourlength;
i_shortcontours = find(i_shortcontours);

%Plot original and smoothed long contours
figure;
for i=1:length(i_longcontours)
    %Draw original contour in red
    i_contour = contourlength(i_longcontours(i),:);
    d_contour = contours(:,i_contour(2)+1:i_contour(2)+i_contour(1));
    line(d_contour(1,:),d_contour(2,:),'Color','r');
    if (mod(i,10) == 0)
        fprintf('\rProcessing Contour %d of %d',i,length(i_longcontours));
    end
    
    %Smooth contour - constant mode
    if strcmp(smooth_mode,'const')
        %Check if contour is closed
        if norm(d_contour(:,1)-d_contour(:,end)) > 1
            %Normal smooth for open contours
            d_contour(1,:) = smooth(d_contour(1,:),smooth_span);
            d_contour(2,:) = smooth(d_contour(2,:),smooth_span);
            line(d_contour(1,:),d_contour(2,:),'Color',[0.6 0.4 0.3],'LineWidth',2.0);
        else
            %Closed contours are extended with wraparound data before smoothing
            d_contour_ext = [smooth([d_contour(1,end-loopovr:end-1),d_contour(1,1:end-1),d_contour(1,1:loopovr+1)],smooth_span)';...
                smooth([d_contour(2,end-loopovr:end-1),d_contour(2,1:end-1),d_contour(2,1:loopovr+1)],smooth_span)'];
            d_contour = d_contour_ext(:,loopovr+1:end-loopovr);
            line(d_contour(1,:),d_contour(2,:),'Color',[0.6 0.4 0.3],'LineWidth',2.0);
            text(d_contour(1,1),d_contour(2,1),num2str(i));
        end
    end
    
    %Smooth contour - gradient adaptive mode
     if strcmp(smooth_mode,'grad')
        %Check if contour is closed
        if norm(d_contour(:,1)-d_contour(:,end)) > 1
            window_exp_i = min(length(d_contour)-1,window_exp); %Limit expansion window to length of contour
            %Reflect ends of linear contours
            d_contour_ext = [bsxfun(@minus,2*d_contour(:,1),d_contour(:,window_exp_i:-1:1)),d_contour,bsxfun(@minus,2*d_contour(:,end),d_contour(:,end-window_exp_i:end))];
            
            for j=window_exp_i+1:length(d_contour)+window_exp_i
               winsize_j=min(floor(winsize(floor(d_contour_ext(2,j)),floor(d_contour_ext(1,j)))/2),window_exp_i);
               d_contour_ext(:,j)=mean(d_contour_ext(:,j-winsize_j:j+winsize_j),2);
            end
            
            d_contour = d_contour_ext(:,window_exp_i:end-window_exp_i);
            line(d_contour(1,:),d_contour(2,:),'Color',[0.6 0.4 0.3],'LineWidth',2.0);
        else
            window_exp_i = min(length(d_contour)-2,window_exp); %Limit expansion window to length of contour
            %Closed contours are extended with wraparound data before smoothing
            d_contour_ext = [d_contour(:,end-(window_exp_i+1):end-1),d_contour(:,1:end-1),d_contour(:,1:window_exp_i)];
            
            for j=window_exp_i+1:length(d_contour)+window_exp_i
               winsize_j=min(floor(winsize(floor(d_contour_ext(2,j)),floor(d_contour_ext(1,j)))/2),window_exp_i);
               d_contour_ext(:,j)=mean(d_contour_ext(:,j-winsize_j:j+winsize_j),2);
            end            
            
            d_contour = d_contour_ext(:,window_exp_i:end-window_exp_i);
            line(d_contour(1,:),d_contour(2,:),'Color',[0.6 0.4 0.3],'LineWidth',2.0);
            text(d_contour(1,1),d_contour(2,1),num2str(i));
        end
     end
    
    %Output contour
    way = docNode.createElement('way');
    way.setAttribute('id',num2str(idcount));
    wayroot.appendChild(way);
    idcount = idcount + 1;
    
    for j=1:length(d_contour)
        node = docNode.createElement('node');
        node.setAttribute('id',num2str(idcount));
        noderoot.appendChild(way);
        idcount = idcount + 1;
    end
    
    
end

%Plot short contours
for i=1:length(i_shortcontours)
    i_contour = contourlength(i_shortcontours(i),:);
    d_contour = contours(:,i_contour(2)+1:i_contour(2)+i_contour(1));
    line(d_contour(1,:),d_contour(2,:),'Color','r');
end
    
    